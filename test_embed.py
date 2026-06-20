import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

models_to_test = [
    "models/embedding-001",
    "text-embedding-004",
    "models/text-embedding-004",
    "gemini-embedding-001",
    "models/gemini-embedding-001"
]

for m in models_to_test:
    print(f"Testing {m}...")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=m)
        vector = embeddings.embed_query("Hello world")
        print(f"SUCCESS with {m}")
        break
    except Exception as e:
        print(f"FAILED with {m}: {str(e)[:100]}")
