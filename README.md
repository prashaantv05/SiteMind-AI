# SiteMind AI 🧠✨

SiteMind AI is a highly professional, full-stack **Retrieval-Augmented Generation (RAG)** web application that allows users to instantly chat with the contents of any website. 

By pasting a URL, the system dynamically scrapes, processes, and embeds the website's text into a local vector database. Users can then ask highly specific questions, and the AI will answer accurately using *only* the retrieved context from the website, completely eliminating AI hallucinations.

## ✨ Features
*   **Dynamic Web Scraping:** Automatically extracts and cleans raw text from provided URLs.
*   **Advanced RAG Pipeline:** Uses LangChain for intelligent semantic text chunking.
*   **Vector Caching:** Utilizes Facebook's FAISS for lightning-fast similarity search and vector storage.
*   **Multi-Tenant Architecture:** Secure Flask backend with isolated user accounts and independent vector databases per user.
*   **Premium Neumorphic UI:** A stunning, fully responsive frontend featuring 3D claymorphic buttons, gold and black luxury gradients, and hardware-accelerated CSS flip animations.
*   **Zero Hallucinations:** Powered by Google's Gemini LLM, bound by a strict prompt template to only answer using the retrieved website context.

## 🛠️ Technology Stack
*   **Backend:** Python, Flask, SQLite
*   **AI / Machine Learning:** LangChain, Google Gemini API (LLM & Embeddings), FAISS Vector DB
*   **Web Scraping:** BeautifulSoup4, Requests
*   **Frontend:** HTML5, Vanilla CSS (Neumorphism), JavaScript

## 🏗️ System Architecture

```mermaid
graph TD
    User(("User"))
    Web["Target Website"]
    
    subgraph "1. Data Ingestion Pipeline"
        Scraper["HTML Scraper (BeautifulSoup)"]
        Splitter["Text Chunking (LangChain)"]
        Embedder["Embedding Model (Gemini)"]
        VectorDB[("FAISS Vector DB")]
    end

    subgraph "2. Retrieval-Augmented Generation"
        Retriever["Similarity Search"]
        Prompt["Strict Context Prompt"]
        LLM["Gemini LLM"]
    end

    %% Ingestion Flow
    Web -->|"Extract Text"| Scraper
    Scraper -->|"Clean Data"| Splitter
    Splitter -->|"Text Chunks"| Embedder
    Embedder -->|"Vector Embeddings"| VectorDB

    %% Query Flow
    User -->|"Asks Question"| Retriever
    Retriever -->|"Searches"| VectorDB
    VectorDB -->|"Top Context Matches"| Prompt
    Prompt -->|"Context + Question"| LLM
    LLM -->|"Accurate Answer"| User
```

## 🚀 Local Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sitemind-ai.git
   cd sitemind-ai
   ```

2. **Set up your API Key**
   You will need a Google Gemini API key. Set it as an environment variable in your terminal:
   ```bash
   # Windows
   set GOOGLE_API_KEY="your_api_key_here"
   
   # Mac/Linux
   export GOOGLE_API_KEY="your_api_key_here"
   ```

3. **Install Dependencies**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure you have flask, langchain, google-generativeai, faiss-cpu, and beautifulsoup4 installed)*

4. **Run the Server**
   ```bash
   python server.py
   ```
   The application will be running at `http://127.0.0.1:5000`.

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
