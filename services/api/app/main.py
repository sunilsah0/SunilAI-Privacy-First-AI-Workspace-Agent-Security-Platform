from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import User
from .security import hash_password, verify_password, create_token, read_token
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from .models import User, Document

Base.metadata.create_all(engine)  # temporary; we switch to migrations in Phase 3
app = FastAPI(title="VerityAI")
bearer = HTTPBearer()

class Creds(BaseModel):
    email: EmailStr
    password: str

def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    try:
        uid = read_token(cred.credentials)
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user

@app.post("/auth/register", status_code=201)
def register(c: Creds, db: Session = Depends(get_db)):
    if len(c.password) < 10:
        raise HTTPException(400, "Password must be at least 10 characters")
    if db.scalar(select(User).where(User.email == c.email)):
        raise HTTPException(409, "Email already registered")
    db.add(User(email=c.email, password_hash=hash_password(c.password)))
    db.commit()
    return {"ok": True}

@app.post("/auth/login")
def login(c: Creds, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == c.email))
    if not user or not verify_password(c.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")  # same message for both cases
    return {"access_token": create_token(user.id)}

@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": str(user.id), "email": user.email}

class DocIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(max_length=100_000)
    
def get_my_document(doc_id: UUID, user: User, db: Session) -> Document:
    """The ONE place that decides if you may touch a document."""
    doc = db.scalar(
        select(Document).where(Document.id == doc_id, Document.owner_id == user.id)
    )
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc

@app.post("/documents", status_code=201)
def create_document(d: DocIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = Document(owner_id=user.id, title=d.title, content=d.content)
    db.add(doc)
    db.commit()
    return {"id": str(doc.id), "title": doc.title}

@app.get("/documents")
def list_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    docs = db.scalars(select(Document).where(Document.owner_id == user.id)).all()
    return [{"id": str(x.id), "title": x.title} for x in docs]

@app.get("/documents/{doc_id}")
def read_document(doc_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = get_my_document(doc_id, user, db)
    return {"id": str(doc.id), "title": doc.title, "content": doc.content}

@app.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = get_my_document(doc_id, user, db)
    db.delete(doc)
    db.commit()