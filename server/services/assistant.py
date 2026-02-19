import os
from openai import OpenAI
from services.database import get_collection
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_policy(question):
    collection = get_collection()

    # Booster queries — cast a wider net with different phrasings
    booster_queries = [
        question,
        f"plan coverage limit {question}",
        f"table data {question}",
        "pre-existing conditions stable months all plans"
    ]

    seen = set()
    documents = []
    metadatas = []
    context_with_pages = ""

    for query in booster_queries:
        results = collection.query(
            query_texts = [query],
            n_results = 5,
        )
        for  (doc,meta) in (zip(results["documents"][0], results["metadatas"][0])):
            if doc not in seen:
                seen.add(doc)
                documents.append(doc)
                metadatas.append(meta)
                page_num = meta.get("page", "Unknown")
                context_with_pages += f"[Page {page_num}]: {doc}\n\n"

    system_message = (
    "You are an expert insurance assistant for Manulife Travel Insurance. "
    "Answer strictly based on the provided context. "
    "\n\n### TABLE RULES:\n"
    "Plan columns appear in this order (from left to right after the 'Feature' column):\n"
    "- Single-Trip Medical: [1] Emergency Medical, [2] TravelEase\n"
    "- Single-Trip Non-Medical: [1] Trip Cancellation, [2] Non-Medical Inclusive\n"
    "- Single-Trip All-Inclusive: [1] All-Inclusive, [2] Youth, [3] Youth Deluxe\n"
    "- Multi-Trip: [1] Medical, [2] TravelEase, [3] All-Inclusive\n"
    "\n### LOGIC HINT:\n"
    "- 'Delayed return' covers $150/day for meals/hotel.\n"
    "- IMPORTANT: Quarantine is EXCLUDED in Canada, but COVERED internationally (e.g., Mexico) under 'Delayed return'.\n"
    "\nAlways cite page numbers (Page X). If unsure, say you cannot find the info.\n"
    "\nOnly speak from the provided context.If the answer is not explicitly word-for-word in the provided context, you MUST say exactly: 'I'm sorry, I cannot find the specific information in the policy documents.'"
    )

    user_message = (
        f"CONTEXT:\n{context_with_pages}\n\n"
        f"QUESTION: {question}\n\n"
        "INSTRUCTION: First, identify the potential benefit. Second, check ALL provided text for exclusions "
        "that might apply to this specific scenario. Finally, provide your answer."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=0
    )

    return response.choices[0].message.content

