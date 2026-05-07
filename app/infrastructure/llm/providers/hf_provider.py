import asyncio
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from langfuse import observe
from app.infrastructure.llm.base import LLMProvider


class HuggingFaceLocal(LLMProvider):
    def __init__(self, model_id: str, adapter_id: str = None, token: str = None):

        print(f"Initializing Local QLoRA Model: {model_id}")

        # For Linux/Mac
        # # 1. QLoRA Configuration
        # bnb_config = BitsAndBytesConfig(
        #     load_in_4bit=True,
        #     bnb_4bit_use_double_quant=True,
        #     bnb_4bit_quant_type="nf4",
        #     bnb_4bit_compute_dtype=torch.float16,
        # )

        # # 2. Load Base Model
        # base_model = AutoModelForCausalLM.from_pretrained(
        #     model_id, quantization_config=bnb_config, device_map="auto", token=token
        # )

        self.tokenizer = AutoTokenizer.from_pretrained(model_id, token=token)

        # For windows (bitsandbytes not supported)
        base_model = AutoModelForCausalLM.from_pretrained(
            model_id, device_map="auto")

        # 3. Load Adapter (The QLoRA part)
        if adapter_id:
            print(f"Loading Adapter: {adapter_id}")
            self.model = PeftModel.from_pretrained(base_model, adapter_id)
        else:
            self.model = base_model

        self.model.eval()

    def _messages_to_prompt(self, messages):
        # return self.tokenizer.apply_chat_template(
        #     messages,
        #     tokenize=False,
        #     add_generation_prompt=True
        # )
        return "\n".join(
            f"{m['role'].capitalize()}: {m['content']}"
            for m in messages
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
                max_new_tokens=150,
                tokenizer=self.tokenizer,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode only the new part
        new_tokens = outputs[0][input_length:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        # return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
