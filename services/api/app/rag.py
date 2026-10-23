import io
from pypdf import PdfReader
from sqlalchemy import select
from .models import Chunk, Document

def extract_text(filename: str, data: bytes) -> str:
    """Treat every file as untrusted. Only a few simple formats for now."""
    name = filename.lower()
    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="replace")
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    raise ValueError("unsupported file type")

def split_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Cut text into overlapping pieces so ideas are not cut in half."""
    text = text.strip()
    chunks, start = [], 0
    while start < len(text):
        piece = text[start:start + size].strip()
        if piece:
            chunks.append(piece)
        start += size - overlap
    return chunks

def search_chunks(db, user_id, provider, query: str, k: int = 4) -> list[dict]:
    query_vector = provider.embed([query])[0]
    distance = Chunk.embedding.cosine_distance(query_vector)
    rows = db.execute(
        select(Chunk.content, Chunk.document_id, Document.title, distance.label("distance"))
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.owner_id == user_id)   # Python check; Postgres RLS is the second check
        .order_by(distance)
        .limit(k)
    ).all()
    return [
        {"document_id": str(r.document_id), "title": r.title,
         "text": r.content, "distance": float(r.distance)}
        for r in rows
    ]