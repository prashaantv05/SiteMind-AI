import config
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def split_text_into_chunks(text: str) -> list[str]:
    """Splits a large block of text into smaller, overlapping chunks."""
    if not text:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
    )
    
    chunks = text_splitter.split_text(text)
    return chunks

def get_gemini_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    """Initializes and returns the Gemini Embedding model."""
    if not config.GEMINI_API_KEY:
        print("Warning: API key not found in environment or .env file.")
        
    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL_NAME,
        google_api_key=config.GEMINI_API_KEY
    )
    return embeddings

# Simple test block
if __name__ == "__main__":
    print("Testing Embedding Model initialization...")
    try:
        model = get_gemini_embeddings_model()
        # Test it on a small word to see if it works
        test_vector = model.embed_query("Hello world")
        print("Success! Gemini Embeddings model is ready.")
        print(f"Generated a vector with {len(test_vector)} dimensions.")
    except Exception as e:
        print(f"Failed to initialize or run the embeddings model. Error: {e}")
