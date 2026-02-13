import google.generativeai as genai
from dotenv import load_dotenv
import os

# load env
load_dotenv()
# load key from env
gemini_key = os.getenv("GEMINI_API_KEY")

# check if key is detected or no
if gemini_key is None: 
    raise ValueError("API Key tidak ditemukan! Pastikan .env kamu benar.")
else:
    print(gemini_key)
    
genai.configure(api_key=gemini_key)

model = genai.GenerativeModel("gemini-2.5-flash")

# x = input('apa pertanyaan yang kamu pengen tanya dengan gemini AI?')
# print('Pertanyaan kamu: ' + x)


# response = model.generate_content(x)

# print(response.text)