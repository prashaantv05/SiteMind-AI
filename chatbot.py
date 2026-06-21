import os
from dotenv import load_dotenv
import config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load the API key from the .env file
load_dotenv()

# This is the strict set of rules we are giving to Gemini.
# By providing the context and the question here, Gemini knows exactly what to read.
PROMPT_TEMPLATE = """You are a highly knowledgeable but incredibly friendly, casual, and conversational AI assistant. You should talk to the user like they are your close friend. Use a warm, enthusiastic tone, keep things relatively concise, and don't be afraid to use an occasional emoji!

Your primary goal is to answer questions based strictly on the provided Context from the indexed website. 

However, if the user asks a general knowledge question or a casual greeting, you should:
1. Politely and casually mention that the specific info isn't in the website context (skip this for simple greetings).
2. Go ahead and answer the question anyway using your own general knowledge, keeping the friendly and helpful vibe.

Recent Chat History:
{chat_history}

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

def generate_answer(query: str, context: str, chat_history: str, llm: ChatGoogleGenerativeAI):
    """Generates an answer using streaming output and conversation history."""
    if not context or not context.strip():
        yield "I couldn't find that information on the indexed website."
        return
        
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["chat_history", "context", "question"]
    )
    
    final_prompt = prompt.format(chat_history=chat_history, context=context, question=query)
    
    try:
        # We use .stream() instead of .invoke() so we can yield word-by-word
        for chunk in llm.stream(final_prompt):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        yield f"Error communicating with Gemini LLM: {e}"

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
