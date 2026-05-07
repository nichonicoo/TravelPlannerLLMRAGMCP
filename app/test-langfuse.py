import os
from dotenv import load_dotenv
from langfuse import observe, get_client

# 1. Load your keys
load_dotenv()
langfuse = get_client()

# 2. A simple function to test the connection
@observe(name="test_connection of langfuse")
def test_connection():
    print(f"Testing Langfuse connection")
    return f"Success!"

if __name__ == "__main__":
    # 3. Trigger the function
    result = test_connection()
    print(result)
