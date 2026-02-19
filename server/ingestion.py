import os
import pdfplumber
from models.policy import PolicyChunk
import re
import json


def smart_chunker(text,source_name,current_page, chunk_size=1500, chunk_overlap=500):
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, len(text))

        if end < text_length:
            last_newline = text.rfind('\n', start, end)
            if last_newline != -1 and last_newline > start + (chunk_size // 2):
                end = last_newline

        chunk = text[start:end].strip()

        chunks.append(PolicyChunk(
            text=chunk,
            source=source_name,
            page=current_page,
            metadata={"char_start": start, "char_end": end}
        ))

        new_start = end - chunk_overlap
        if new_start <= start:
            start = end
        else:
            start = new_start

    return chunks

def extract_text_to_chunks(file_path,filename):
    final_chunks = []
    
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):

            # 1. Extract regular text
            # Note: raw_text may contain table data which also appears in table_markdown below.
            # This duplication is intentional — raw_text aids semantic retrieval while
            # table_markdown preserves column structure for accurate answer generation.
            raw_text = page.extract_text() or ""

            cleaned_raw_text = filter_header_footer(raw_text)

            # 2. Extract and format tables
            tables = page.extract_tables()   
            table_markdown = ""
            
            if tables:
                for table in tables:
                    for row in table:
                        cleaned_row = [str(item).replace('\n', ' ').strip() if item else "" for item in row]
                        table_markdown += f"| {' | '.join(cleaned_row)} |\n"
            
            
            
            # Combine them: prioritize the table structure if it exists
            # 3. STITCH: Combine into one single flow of text
            # We add the Page Title/Header so every chunk knows what document this is
            page_context = f"Page {i+1} - {filename}\n"
            full_content_for_chunking = f"{page_context}\n{cleaned_raw_text}\n\n### DATA TABLE:\n{table_markdown}"
            
            # 3. Chunk this structured data
            page_chunks = smart_chunker(
                text=full_content_for_chunking, 
                source_name=filename, 
                current_page=i + 1,
                chunk_size=1500, # Slightly larger to keep table headers with rows
                chunk_overlap=500
            )
            final_chunks.extend(page_chunks)
            
    return final_chunks


def filter_header_footer(text):
    lines = text.split('\n')
    filtered_lines = []

    junk_phrases = [
        "Manulife Travel Insurance", 
        "Comparison Charts for Travelling Canadians",
        "Back to home",
        "Effective October 2, 2023",
        "Continued on next page"
    ]
    
    for line in lines:
        is_junk = any(junk in line.strip() for junk in junk_phrases)
        if not is_junk:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)
        

def save_chunks_to_json(chunks, output_file="./processed_chunks.json"):
    serializable_chunks = [chunk.model_dump() for chunk in chunks]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(serializable_chunks, f, ensure_ascii=False, indent=4)
    print(f"Saved {len(serializable_chunks)} chunks to {output_file}")



def process_all_policies(directory_path="./data"):
    if not os.path.exists(directory_path):
        print(f"Error: Directory {directory_path} not found.")
        return []
    
    all_final_chunks = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".pdf"):
            print(f"Processing {filename}...")
            file_path = os.path.join(directory_path, filename)
            chunks = extract_text_to_chunks(file_path, filename)
            all_final_chunks.extend(chunks)
    # print(f"Total chunks created: {len(all_final_chunks)}")
    return all_final_chunks



my_chunks = process_all_policies()
save_chunks_to_json(my_chunks)