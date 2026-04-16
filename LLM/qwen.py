import requests
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = "qwen/qwen3-1.7b"
# sesuaiin dengan link LM Studio
# LM_STUDIO_URL = "http://127.0.0.1:1234/api/v1/chat" 
LM_STUDIO_URL = "http://192.168.68.118:1234/api/v1/chat"

# def local_llm_chat(messages, temperature =0):
#     payload = {
#         "model": MODEL_NAME,
#         "input": messages,
#         "temperature": temperature
#     }
    
#     try: 
#         r = requests.post(LM_STUDIO_URL, json=payload, timeout=50)
#         r.raise_for_status()
#         data = r.json()
        
#         for items in data.get("output", []):
#             if items.get("type") == "message":
#                 return items.get("content", "").strip()
#         return None
#     except Exception as e: 
#         print('Local LLM Error', e)
#         return None
    
def chat(messages: str | list, temperature: float =0 ) -> str | None: 
    
    if isinstance(messages, str):
        payload = {
            "model": MODEL_NAME,
            "input": messages,
            "temperature": temperature
        }
    else: 
        payload = {
            "model": MODEL_NAME,
            "input": messages,
            "temperature": temperature
        }
   # ori without reasoning 
    try: 
        r = requests.post(LM_STUDIO_URL, json=payload, timeout=200)
        r.raise_for_status()
        data = r.json()
        
        for items in data.get("output", []):
            if items.get("type") == "message":
                return items.get("content", "").strip()
        return None
    
    except Exception as e: 
        print('Local LLM Error (Qwen):', e)
        return None