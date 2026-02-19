import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv
import json
import os


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")



openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small"
)

def get_collection():
    # Connect to the local folder
    client = chromadb.PersistentClient(path="./policy_db")

    collection = client.get_or_create_collection(
        name="insurance_policy_chunks", 
        embedding_function=openai_ef
    )

    return collection


def sync_data():
    collection = get_collection()

    current_count = collection.count()
    if current_count > 0:
        print(f"Collection already has {current_count} items. Skipping sync.")
        return collection
    
    print("Collection is empty. Starting one-time OpenAI embedding process...")
    # 1. Load the processed chunks from the JSON file
    with open("./processed_chunks.json", "r", encoding="utf-8") as f:
        all_chunks = json.load(f)

    id = []
    metadatas = []
    documents = []

    for i, chunk in enumerate(all_chunks):
        id.append(f"id{i}")
        documents.append(chunk["text"])
        metadatas.append({
            "source": chunk["source"],
            "page": chunk["page"],
        })

    # 2. Add the chunks to the collection
    collection.add(
        ids=id,
        documents=documents, 
        metadatas=metadatas
    )

    print(f"OpenAI Embeddings created and stored in ./policy_db")
    print(f"Added {len(all_chunks)} chunks to the database collection 'insurance_policy_chunks'.")

    return collection


if __name__ == "__main__":
    my_collection = sync_data()