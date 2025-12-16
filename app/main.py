from datetime import timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import Base, engine
from app.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_db,
    get_optional_user,
    get_password_hash,
    require_admin,
)
from app.storage import storage

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Quality Docs Platform")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_first_admin(db: Session):
    if db.query(models.User).count() == 0:
        admin_user = models.User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="admin",
        )
        db.add(admin_user)
        db.commit()


@app.post("/auth/register", response_model=schemas.UserResponse)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user),
):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    ensure_first_admin(db)

    if db.query(models.User).count() > 0 and (current_user is None or current_user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    new_user = models.User(
        username=user.username,
        password_hash=get_password_hash(user.password),
        role=user.role if user.role in {"admin", "user"} else "user",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    ensure_first_admin(db)
    authenticated = authenticate_user(db, user.username, user.password)
    if not authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=settings.token_expire_minutes)
    access_token = create_access_token(data={"sub": authenticated.username}, expires_delta=access_token_expires)
    return schemas.TokenResponse(access_token=access_token)


@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/documents", response_model=schemas.DocumentResponse)
def upload_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    document = db.query(models.Document).filter(models.Document.title == title).first()
    if document is None:
        document = models.Document(
            title=title,
            description=description,
            tags=tags,
            owner_id=current_user.id,
            latest_version=0,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

    document.latest_version += 1
    saved_path = storage.save(file)
    version = models.DocumentVersion(
        document_id=document.id,
        version=document.latest_version,
        filename=saved_path.name,
        original_name=file.filename,
        mime_type=file.content_type,
        uploader_id=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(document)
    db.refresh(version)
    return document


@app.get("/documents", response_model=List[schemas.DocumentResponse])
def list_documents(
    q: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Document)
    if q:
        like = f"%{q}%"
        query = query.filter(models.Document.title.ilike(like) | models.Document.description.ilike(like))
    if tag:
        like = f"%{tag}%"
        query = query.filter(models.Document.tags.ilike(like))
    documents = query.order_by(models.Document.updated_at.desc()).all()
    return documents


@app.get("/documents/{document_id}/versions", response_model=List[schemas.DocumentVersionResponse])
def list_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return (
        db.query(models.DocumentVersion)
        .filter(models.DocumentVersion.document_id == document_id)
        .order_by(models.DocumentVersion.version.desc())
        .all()
    )


@app.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    version: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if version is None:
        version = document.latest_version
    version_row = (
        db.query(models.DocumentVersion)
        .filter(models.DocumentVersion.document_id == document_id, models.DocumentVersion.version == version)
        .first()
    )
    if version_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    file_path = storage.get_path(version_row.filename)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing on server")

    return FileResponse(
        path=file_path,
        media_type=version_row.mime_type or "application/octet-stream",
        filename=version_row.original_name,
    )


@app.get("/")
def healthcheck():
    return {"status": "ok"}
