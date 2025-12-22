import os
from dotenv import load_dotenv

print(f"CWD: {os.getcwd()}")
print(f"Files in CWD: {os.listdir('.')}")

loaded = load_dotenv()
print(f"dotenv loaded: {loaded}")

key = os.getenv("GOOGLE_API_KEY")
if key:
    print(f"API Key found: Yes (Length: {len(key)})")
    print(f"Key starts with: {key[:4]}...")
else:
    print("API Key found: NO")
