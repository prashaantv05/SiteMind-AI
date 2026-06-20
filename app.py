import sys
import os
import shutil
import config
from scraper import scrape_webpage, extract_text
from embedder import split_text_into_chunks, get_gemini_embeddings_model
from retriever import create_and_save_vector_store, search_vector_store, load_vector_store
from chatbot import get_gemini_llm, generate_answer

def read_urls_from_file(filename=config.URLS_FILE_PATH) -> list[str]:
    """Reads a list of URLs from a text file, ignoring blank lines and comments."""
    urls = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('#'):
                    urls.append(clean_line)
    except FileNotFoundError:
        print(f"Warning: {filename} not found.")
    return urls

def main():
    print("=== Welcome to the Website RAG Chatbot ===")
    
    # Step A: Initialize the embedding model early since we need it to load the cache
    print("\n[1/4] Initializing Embedding Model...")
    embeddings_model = get_gemini_embeddings_model()
    
    # Step B: Try to load the database from disk to save time and API costs
    print("\n[2/4] Checking for existing FAISS database cache...")
    vector_store = load_vector_store(embeddings_model)
    
    # If the cache doesn't exist, we must build it from scratch
    if not vector_store:
        print(" -> No existing cache found. Building from scratch...")
        
        urls = read_urls_from_file("urls.txt")
        if not urls:
            print("\nNo URLs found. Please add at least one website to 'urls.txt'.")
            sys.exit(1)
        
        all_chunks = []
        
        print(f"\nProcessing {len(urls)} websites...")
        for url in urls:
            print(f" - Scraping: {url}")
            soup = scrape_webpage(url)
            if soup:
                text = extract_text(soup)
                chunks = split_text_into_chunks(text)
                all_chunks.extend(chunks)
                print(f"   -> Successfully extracted and created {len(chunks)} chunks.")
            else:
                print(f"   -> Failed to fetch. Skipping this URL.")
                
        if not all_chunks:
            print("\nFailed to extract text from any of the provided URLs. Exiting.")
            sys.exit(1)
            
        print(f"\nTotal chunks combined from all websites: {len(all_chunks)}")
        print("\nCreating new FAISS Vector Store...")
        
        vector_store = create_and_save_vector_store(all_chunks, embeddings_model)
        if not vector_store:
            print("Failed to create vector store. Exiting.")
            sys.exit(1)
    else:
        print(" -> Cache loaded successfully! Skipping web scraping and embedding.")
        print("    (To rebuild the database with new URLs, delete the 'faiss_cache' folder).")
        
    # Step C: Initialize the Chat Model
    print("\n[3/4] Initializing Gemini LLM...")
    llm = get_gemini_llm()
    
    print("\n[4/4] Setup Complete! You can now ask questions about the indexed websites.")
    print("Type 'exit' or 'quit' to stop.")
    print("-" * 50)
    
    # The Interactive Console Chatbot Loop
    while True:
        try:
            user_input = input("\nYou: ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            if not user_input.strip():
                continue
                
            context = search_vector_store(vector_store, user_input, top_k=3)
            answer = generate_answer(user_input, context, llm)
            
            print(f"\nBot: {answer}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
