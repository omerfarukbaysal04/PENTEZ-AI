import requests

url = "http://localhost:11434/api/generate"
payload = {
    "model": "llama3.1:latest",
    "prompt": "merhaba",
    "stream": False
}

response = requests.post(url, json=payload, timeout=60)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")