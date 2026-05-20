import asyncio
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from langfuse import observe
from app.infrastructure.llm.base import LLMProvider


class HuggingFaceLocal(LLMProvider):
    def __init__(self, model_id: str, adapter_id: str = None, token: str = None):
        print(f"Initializing Local QLoRA Model Matrix: {model_id}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_id, token=token)

        # Check if GPU is accessible (Colab Linux environment vs Windows local CPU testing)
        if torch.cuda.is_available():
            print("CUDA environment detected. Booting with 4-bit QLoRA compression...")
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
                token=token
            )
        else:
            print(
                "CUDA unavailable. Falling back to local precision environment architecture...")
            base_model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                token=token
            )

        # 3. Seamlessly graft the QLoRA Adapter on top of Base
        if adapter_id:
            print(f"Loading Adapter: {adapter_id}")
            self.model = PeftModel.from_pretrained(
                base_model, adapter_id, token=token)
        else:
            print("No adapter provided. Proceeding with pure base model layers.")
            self.model = base_model

        self.model.eval()

    def _messages_to_prompt(self, messages):
        # Crucial: Use Qwen's native ChatML structure to ensure high-grade context extraction
        # Transforming objects/dicts into standard structures compatible with apply_chat_template
        formatted_messages = [
            {"role": m.role if hasattr(m, 'role') else m['role'],
             "content": m.content if hasattr(m, 'content') else m['content']}
            for m in messages
        ]
        return self.tokenizer.apply_chat_template(
            formatted_messages,
            tokenize=False,
            add_generation_prompt=True
        )

    @observe(name="hf-generation", as_type="generation")
    async def generate(self, messages) -> str:
        prompt = self._messages_to_prompt(messages)
        return await asyncio.to_thread(self._generate_sync, prompt)

    def _generate_sync(self, prompt: str) -> str:
        inputs = self.tokenizer(
            prompt, return_tensors="pt").to(self.model.device)
        input_length = inputs.input_ids.shape[1]

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                # max_new_tokens=1024,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decodes cleanly starting precisely where the model's generated text response begins
        new_tokens = outputs[0][input_length:]
        response = self.tokenizer.decode(
                new_tokens,
                skip_special_tokens=True
            ).strip()

        # IMPORTANT: Clean up GPU memory immediately after generation
        del outputs
        del inputs

        torch.cuda.empty_cache()

        return response
