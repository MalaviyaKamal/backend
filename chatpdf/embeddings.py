from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
def get_embeddings(text):
    try:
        # Assuming you have the API key stored in a SecretStr object
        google_api_key="AIzaSyD_BCQn7CjSfDqqwe-KUQeE5JWgXf0xTpM"

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.environ.get("GEMINAI_API_KEY"))
        vector = embeddings.embed_query(text)
        print("vector", vector)
        return vector
    except Exception as e:
        print(f"Error calling Google Generative AI embeddings API: {e}")
        raise  # Re-raise the exception for further handling