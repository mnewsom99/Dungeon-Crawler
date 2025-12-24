import ollama
try:
    print("Testing Ollama...")
    res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': 'hi'}])
    print("Success:")
    print(res)
except Exception as e:
    print(f"Failed: {e}")
