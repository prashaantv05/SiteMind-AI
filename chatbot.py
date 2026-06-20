import os
from dotenv import load_dotenv
import config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load the API key from the .env file
load_dotenv()

# This is the strict set of rules we are giving to Gemini.
# By providing the context and the question here, Gemini knows exactly what to read.
PROMPT_TEMPLATE = """You are a helpful, conversational AI assistant.

Your primary goal is to answer questions based strictly on the provided Context from the indexed website. 

However, if the user asks a general knowledge question (e.g., "What is AI?", "Explain quantum physics") or a casual greeting (e.g., "hello", "hi"), you should:
1. Politely state that the specific information isn't in the provided website context (skip this for simple greetings).
2. Go ahead and answer the question anyway using your own general knowledge.

Context:
{context}

Question:
{question}

Answer:"""

def get_gemini_llm() -> ChatGoogleGenerativeAI:
    """Initializes the Gemini Large Language Model."""
    if not config.GEMINI_API_KEY:
        print("Warning: API key not found in environment or .env file.")
    
    llm = ChatGoogleGenerativeAI(
        model=config.LLM_MODEL_NAME,
        temperature=config.LLM_TEMPERATURE,
        google_api_key=config.GEMINI_API_KEY
    )
    return llm

def generate_answer(query: str, context: str, llm: ChatGoogleGenerativeAI) -> str:
    """Generates an answer based on the provided context."""
    if not context or not context.strip():
        return "I couldn't find that information on the indexed website."
        
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )
    
    final_prompt = prompt.format(context=context, question=query)
    
    try:
        response = llm.invoke(final_prompt)
        return response.content
    except Exception as e:
        return f"Error communicating with Gemini LLM: {e}"

# Simple test block
if __name__ == "__main__":
    print("Testing Gemini LLM Initialization...")
    try:
        test_llm = get_gemini_llm()
        dummy_context = "The sky is blue because of Rayleigh scattering."
        dummy_question = "Why is the sky blue?"
        
        print("Sending test question to Gemini...")
        answer = generate_answer(dummy_question, dummy_context, test_llm)
        print(f"\nGemini Answer: {answer}")
        
        # Test out-of-context question
        bad_question = "What is the capital of France?"
        print(f"\nAsking an out-of-context question: '{bad_question}'")
        answer_2 = generate_answer(bad_question, dummy_context, test_llm)
        print(f"Gemini Answer: {answer_2}")
        
    except Exception as e:
        print(f"Failed. Error: {e}")
