import os
import config
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def get_cache_path(chat_id: int) -> str:
    """Helper function to get the unique cache path for a chat."""
    return os.path.join(config.FAISS_CACHE_PATH, str(chat_id))

def create_and_save_vector_store(chunks: list[str], embeddings_model: GoogleGenerativeAIEmbeddings, chat_id: int) -> FAISS:
    """Generates embeddings for all text chunks and stores them in a FAISS vector database."""
    if not chunks:
        print("No text chunks provided. Cannot create vector store.")
        return None
        
    print(f"Generating embeddings for {len(chunks)} chunks and creating FAISS index...")
    
    vector_store = FAISS.from_texts(texts=chunks, embedding=embeddings_model)
    
    cache_path = get_cache_path(chat_id)
    os.makedirs(cache_path, exist_ok=True)
    vector_store.save_local(cache_path)
    
    print(f"FAISS vector store successfully saved to '{cache_path}'")
    return vector_store

def load_vector_store(embeddings_model: GoogleGenerativeAIEmbeddings, chat_id: int) -> FAISS:
    """Loads an existing FAISS vector store from the local disk."""
    cache_path = get_cache_path(chat_id)
    if not os.path.exists(cache_path):
        return None
        
    print(f"Loading existing FAISS vector store from '{cache_path}'...")
    try:
        vector_store = FAISS.load_local(
            folder_path=cache_path, 
            embeddings=embeddings_model, 
            allow_dangerous_deserialization=True
        )
        return vector_store
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None

def search_vector_store(vector_store: FAISS, query: str, top_k: int = config.TOP_K_RESULTS) -> str:
    """Searches the FAISS database for text chunks most similar to the user's question."""
    if not vector_store:
        return ""
        
    print(f"Searching database for context related to: '{query}'...")
    
    matching_docs = vector_store.similarity_search(query, k=top_k)
    context_chunks = [doc.page_content for doc in matching_docs]
    combined_context = "\n\n".join(context_chunks)
    
    return combined_context
