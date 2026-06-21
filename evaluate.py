import os
import re
import config
from scraper import scrape_webpage, extract_text
from embedder import split_text_into_chunks, get_gemini_embeddings_model
from retriever import create_and_save_vector_store, search_vector_store
from chatbot import get_gemini_llm, generate_answer
from langchain_core.prompts import PromptTemplate

# Initialize Models
embeddings_model = get_gemini_embeddings_model()
llm = get_gemini_llm()

# --- EVALUATION PROMPTS (LLM-as-a-Judge) ---

FAITHFULNESS_PROMPT = """You are an impartial judge evaluating a RAG system.
Your task is to measure FAITHFULNESS: Does the Answer hallucinate, or is every factual claim derived from the Context?

Question: {question}
Context: {context}
Answer: {answer}

Provide a score from 0.0 to 1.0. 
1.0 means completely faithful to the context. 
0.0 means the answer is completely hallucinated or contradicts the context.

Respond ONLY with a JSON object in this format: {{"score": 1.0}}"""

ANSWER_RELEVANCE_PROMPT = """You are an impartial judge evaluating a RAG system.
Your task is to measure ANSWER RELEVANCE: Does the Answer directly address the User's Question?

Question: {question}
Answer: {answer}

Provide a score from 0.0 to 1.0. 
1.0 means perfectly answers the question. 
0.0 means completely irrelevant or evasive.

Respond ONLY with a JSON object in this format: {{"score": 1.0}}"""

CONTEXT_RELEVANCE_PROMPT = """You are an impartial judge evaluating a RAG system.
Your task is to measure CONTEXT RELEVANCE: Did the retrieval system fetch context that is actually useful for answering the Question?

Question: {question}
Context: {context}

Provide a score from 0.0 to 1.0. 
1.0 means the context contains the exact answer. 
0.0 means the context is completely useless for this question.

Respond ONLY with a JSON object in this format: {{"score": 1.0}}"""

def extract_score(text: str) -> float:
    """Uses Regex to extract a decimal score from the LLM JSON response."""
    match = re.search(r'"score"\s*:\s*([0-9.]+)', text)
    if match:
        return float(match.group(1))
    return 0.0

def evaluate_metric(prompt_template: str, kwargs: dict) -> float:
    """Runs a single evaluation metric using the LLM-Judge."""
    prompt = PromptTemplate.from_template(prompt_template)
    final_prompt = prompt.format(**kwargs)
    response = llm.invoke(final_prompt)
    return extract_score(response.content)

def run_evaluation():
    print("Starting Automated RAG Evaluation...")
    print("-" * 50)
    
    # 1. Define Test Data
    test_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    test_question = "What programming paradigms does Python support?"
    
    print(f"Target URL: {test_url}")
    print(f"Test Question: {test_question}\n")
    
    # 2. Run Pipeline (Ingestion)
    print("[1/3] Ingesting and Vectorizing data...")
    soup = scrape_webpage(test_url)
    text = extract_text(soup)
    chunks = split_text_into_chunks(text)
    
    # To avoid hitting the Gemini Free-Tier Rate Limits (429 RESOURCE_EXHAUSTED),
    # we will only use the first 10 chunks of the website for this evaluation test.
    chunks = chunks[:10]
    
    # Use a dummy chat_id for evaluation
    eval_chat_id = 9999 
    vector_store = create_and_save_vector_store(chunks, embeddings_model, eval_chat_id)
    
    # 3. Run Pipeline (Retrieval)
    print("[2/3] Retrieving Context...")
    context = search_vector_store(vector_store, test_question, top_k=3)
    
    # 4. Run Pipeline (Generation)
    print("[3/3] Generating Answer...")
    # Our generate_answer returns a stream generator, so we must join it
    answer_generator = generate_answer(test_question, context, chat_history="", llm=llm)
    answer = "".join(list(answer_generator))
    
    print("\n" + "=" * 50)
    print(f"GENERATED ANSWER:\n{answer}")
    print("=" * 50 + "\n")
    
    # 5. Evaluate Metrics
    print("Judging Results...")
    
    faithfulness_score = evaluate_metric(FAITHFULNESS_PROMPT, {
        "question": test_question, 
        "context": context, 
        "answer": answer
    })
    
    relevance_score = evaluate_metric(ANSWER_RELEVANCE_PROMPT, {
        "question": test_question, 
        "answer": answer
    })
    
    context_score = evaluate_metric(CONTEXT_RELEVANCE_PROMPT, {
        "question": test_question, 
        "context": context
    })
    
    # 6. Print Report
    print("\n--- RAG EVALUATION REPORT ---")
    print("-" * 25)
    print(f"Context Relevance: {context_score:.1f} / 1.0 (Did we fetch good data?)")
    print(f"Faithfulness:      {faithfulness_score:.1f} / 1.0 (Did it hallucinate?)")
    print(f"Answer Relevance:  {relevance_score:.1f} / 1.0 (Did it answer the question?)")
    
    overall = (context_score + faithfulness_score + relevance_score) / 3.0
    print(f"\nOverall Score:     {overall:.2f} / 1.0")

if __name__ == "__main__":
    run_evaluation()
