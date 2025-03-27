from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
import openai
import faiss
import numpy as np
import os
import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Fixed to match frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY") or "your-openai-api-key-here"

# FAISS index setup
dimension = 1536  # OpenAI embedding dimension
index = faiss.IndexFlatL2(dimension)
chunks = []

# Temporary storage for PDF texts
pdf_texts = []

@app.post("/upload_pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    logger.debug(f"Received {len(files)} files for upload")
    global pdf_texts
    try:
        for file in files:
            logger.debug(f"Processing file: {file.filename}")
            pdf_reader = PdfReader(file.file)
            text = ""
            for page in pdf_reader.pages:
                extracted_text = page.extract_text()
                text += extracted_text if extracted_text else ""
            logger.debug(f"Extracted {len(text)} characters from {file.filename}")
            pdf_texts.append(text)  # Store the extracted text
        logger.info(f"Successfully uploaded {len(files)} PDFs")
        return {"message": f"Uploaded {len(files)} PDFs successfully"}
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        for file in files:
            await file.close()

@app.post("/process_pdfs")
async def process_pdfs():
    logger.debug("Processing PDFs to create embeddings")
    global pdf_texts, index, chunks
    try:
        if not pdf_texts:
            raise HTTPException(status_code=400, detail="No PDFs to process")
        
        for text in pdf_texts:
            chunk_size = 1000
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                chunks.append(chunk)
                response = openai.Embedding.create(
                    input=chunk,
                    model="text-embedding-ada-002"
                )
                embedding = response["data"][0]["embedding"]
                index.add(np.array([embedding], dtype="float32"))
        
        pdf_texts = []  # Clear the stored texts after processing
        logger.info("Successfully created vector embeddings")
        return {"message": "Vector embeddings created"}
    except Exception as e:
        logger.error(f"Embedding creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Embedding creation failed: {str(e)}")

@app.post("/query")
async def query(data: dict):
    logger.debug(f"Received query: {data}")
    try:
        query = data.get("query")
        use_vector_db = data.get("useVectorDB", False)
        use_llm = data.get("useLLM", False)

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        if not use_llm:
            return {"answer": "LLM is not connected"}

        if use_vector_db:
            logger.debug(f"FAISS index size: {index.ntotal}")
        if use_vector_db and index.ntotal > 0:
            response = openai.Embedding.create(input=query, model="text-embedding-ada-002")
            query_embedding = np.array([response["data"][0]["embedding"]], dtype="float32")
            distances, indices = index.search(query_embedding, 3)
            relevant_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]
            context = "\n".join(relevant_chunks)
            prompt = f"Based on the following documents:\n{context}\n\nAnswer the query: {query}"
        else:
            prompt = query

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        return {"answer": response.choices[0].text.strip()}
    except Exception as e:
        logger.error(f"Query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)