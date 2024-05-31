import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def get_embeddings(text):
    api_key = "AIzaSyD_BCQn7CjSfDqqwe-KUQeE5JWgXf0xTpM"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "text-embedding-ada-002",
        "input": text.replace("\n", " ")
    }
    
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["POST"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    
    try:
        response = session.post(
            "https://api.gemini.ai/v1/embeddings",  
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        return result['data'][0]['embedding']
    except requests.RequestException as e:
        print(f"Error calling GeminAI embeddings API: {e}")
        raise



