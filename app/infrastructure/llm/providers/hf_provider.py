import asyncio
import time
from threading import Thread
import gc
import torch
import torch.nn.functional as F

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TextIteratorStreamer,
)

from peft import PeftModel
from langfuse import observe

from app.infrastructure.llm.base import LLMProvider


class HuggingFaceLocal(LLMProvider):

    def __init__(
        self,
        model_id: str,
        adapter_id: str = None,
        token: str = None,
    ):
        print(f"Initializing Local QLoRA Model Matrix: {model_id}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            token=token
        )

        if torch.cuda.is_available():
            print("CUDA detected → loading 4-bit QLoRA stack")

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )

            base_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                quantization_config=bnb_config,
                device_map="auto",
                token=token,
            )

        else:
            print("CUDA unavailable → fallback precision mode")

            base_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                token=token,
            )

        if adapter_id:
            print(f"Loading PEFT Adapter: {adapter_id}")

            self.model = PeftModel.from_pretrained(
                base_model,
                adapter_id,
                token=token,
            )

        else:
            print("No adapter provided. Proceeding with pure base model layers.")
            self.model = base_model

        self.model.eval()

    def _messages_to_prompt(self, messages):

        formatted_messages = [
            {
                "role": (
                    m.role if hasattr(m, "role")
                    else m["role"]
                ),
                "content": (
                    m.content if hasattr(m, "content")
                    else m["content"]
                ),
            }
            for m in messages
        ]

        return self.tokenizer.apply_chat_template(
            formatted_messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    @observe(name="hf-generation", as_type="generation")
    async def generate(
        self,
        messages,
        mode: str = "benchmark",
    ) -> dict:
        prompt = self._messages_to_prompt(messages)

        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            None,
            self._generate_sync,
            prompt,
            mode
        )

    def _generate_sync(
        self,
        prompt: str,
        mode: str = "benchmark",
    ) -> dict:
        if mode not in ["benchmark", "analysis"]:
            raise ValueError(
                f"Unsupported generation mode: {mode}"
            )

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        tokenize_start = time.perf_counter()

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt"
        ).to(self.model.device)

        tokenize_end = time.perf_counter()

        prompt_tokens = inputs.input_ids.shape[1]

        # =====================================================
        # BENCHMARK MODE
        # =====================================================

        if mode == "benchmark":

            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
            )

            generation_kwargs = dict(
                **inputs,
                streamer=streamer,
                max_new_tokens=4096,
                do_sample=False,
                use_cache=True,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
            )

            generated_text = ""

            first_token_timestamp = None

            generation_start = time.perf_counter()

            # ---------------------------------------------
            # THREAD TARGET
            # ---------------------------------------------

            def _run_generation():
                with torch.inference_mode():
                    self.model.generate(
                        **generation_kwargs
                    )

            generation_thread = Thread(
                target=_run_generation
            )

            generation_thread.start()

            # ---------------------------------------------
            # STREAM TOKENS
            # ---------------------------------------------

            for chunk in streamer:
                if first_token_timestamp is None:
                    first_token_timestamp = (
                        time.perf_counter()
                    )
                generated_text += chunk

            generation_thread.join()
            generation_end = time.perf_counter()

            # ---------------------------------------------
            # LATENCY METRICS
            # ---------------------------------------------

            total_latency_sec = (
                generation_end - generation_start
            )

            ttft_sec = (
                first_token_timestamp - generation_start
                if first_token_timestamp
                else total_latency_sec
            )

            decode_time_sec = max(
                total_latency_sec - ttft_sec,
                1e-6
            )

            # ---------------------------------------------
            # TOKEN COUNTS
            # ---------------------------------------------

            completion_tokens = len(
                self.tokenizer.encode(
                    generated_text,
                    add_special_tokens=False
                )
            )

            total_tokens = (
                prompt_tokens + completion_tokens
            )

            throughput_tok_sec = (
                completion_tokens / decode_time_sec
            )

            # ---------------------------------------------
            # GPU METRICS
            # ---------------------------------------------

            gpu_peak_mem_mb = None
            gpu_reserved_mem_mb = None

            if torch.cuda.is_available():

                gpu_peak_mem_mb = round(
                    torch.cuda.max_memory_allocated()
                    / (1024 ** 2),
                    2
                )

                gpu_reserved_mem_mb = round(
                    torch.cuda.max_memory_reserved()
                    / (1024 ** 2),
                    2
                )

            # ---------------------------------------------
            # CLEANUP
            # ---------------------------------------------

            del inputs

            gc.collect()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return {
                "response": generated_text.strip(),
                "mode": mode,

                # TOKEN COUNTS
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,

                # TIMING
                "tokenize_sec": round(
                    tokenize_end - tokenize_start,
                    4
                ),

                "ttft_sec": round(
                    ttft_sec,
                    4
                ),

                "decode_time_sec": round(
                    decode_time_sec,
                    4
                ),

                "total_latency_sec": round(
                    total_latency_sec,
                    4
                ),

                "throughput_tok_sec": round(
                    throughput_tok_sec,
                    2
                ),

                # TOKEN ANALYSIS
                "avg_token_confidence": None,
                "avg_token_entropy": None,

                # GPU METRICS
                "gpu_peak_mem_mb": gpu_peak_mem_mb,
                "gpu_reserved_mem_mb": gpu_reserved_mem_mb,
            }

        # =====================================================
        # ANALYSIS MODE
        # =====================================================

        generation_start = time.perf_counter()

        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=False,
                use_cache=True,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.eos_token_id,
                return_dict_in_generate=True,
                output_scores=True,
            )

        generation_end = time.perf_counter()

        total_latency_sec = (
            generation_end - generation_start
        )

        # -------------------------------------------------
        # GENERATED TOKENS
        # -------------------------------------------------
        generated_ids = outputs.sequences[0][prompt_tokens:]

        actual_generated_ids = [
            idx for idx in generated_ids
            if idx.item() != self.tokenizer.pad_token_id
        ]

        generated_text = self.tokenizer.decode(
            actual_generated_ids,
            skip_special_tokens=True
        ).strip()

        completion_tokens = len(actual_generated_ids)

        total_tokens = (
            prompt_tokens + completion_tokens
        )

        # -------------------------------------------------
        # TOKEN CONFIDENCE + ENTROPY
        # -------------------------------------------------

        confidences = []
        entropies = []

        for step, logits in enumerate(outputs.scores):
            if step >= completion_tokens:
                break

            probs = F.softmax(
                logits,
                dim=-1
            )

            log_probs = F.log_softmax(
                logits,
                dim=-1
            )

            entropy = -torch.sum(
                probs * log_probs,
                dim=-1
            ).mean().item()

            entropies.append(entropy)

            actual_token_id = (
                generated_ids[step].item()
            )

            token_prob = probs[
                0,
                actual_token_id
            ].item()

            confidences.append(token_prob)

        avg_confidence = (
            sum(confidences) / len(confidences)
            if confidences else None
        )

        avg_entropy = (
            sum(entropies) / len(entropies)
            if entropies else None
        )

        # -------------------------------------------------
        # GPU METRICS
        # -------------------------------------------------

        gpu_peak_mem_mb = None
        gpu_reserved_mem_mb = None

        if torch.cuda.is_available():
            gpu_peak_mem_mb = round(
                torch.cuda.max_memory_allocated()
                / (1024 ** 2),
                2
            )

            gpu_reserved_mem_mb = round(
                torch.cuda.max_memory_reserved()
                / (1024 ** 2),
                2
            )

        # -------------------------------------------------
        # CLEANUP
        # -------------------------------------------------

        del outputs
        del inputs
        del generated_ids
        del actual_generated_ids

        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return {
            "response": generated_text,
            "mode": mode,

            # TOKEN COUNTS
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,

            # TIMING
            "tokenize_sec": round(
                tokenize_end - tokenize_start,
                4
            ),

            # NOT VALID IN ANALYSIS MODE
            "ttft_sec": None,
            "decode_time_sec": None,
            "throughput_tok_sec": None,

            "total_latency_sec": round(
                total_latency_sec,
                4
            ),

            # TOKEN ANALYSIS
            "avg_token_confidence": round(
                avg_confidence,
                4
            ) if avg_confidence is not None else None,

            "avg_token_entropy": round(
                avg_entropy,
                4
            ) if avg_entropy is not None else None,

            # GPU METRICS
            "gpu_peak_mem_mb": gpu_peak_mem_mb,
            "gpu_reserved_mem_mb": gpu_reserved_mem_mb,
        }
