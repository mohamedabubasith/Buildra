from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import LLMConfig
from ..schemas import LLMConfigIn, LLMConfigOut
from ..services.crypto import encrypt, decrypt

router = APIRouter(tags=["config"])


@router.get("/config", response_model=LLMConfigOut | None)
def get_config(db: Session = Depends(get_db)):
    cfg = db.query(LLMConfig).first()
    if not cfg:
        return None
    return cfg


@router.put("/config", response_model=LLMConfigOut)
def upsert_config(body: LLMConfigIn, db: Session = Depends(get_db)):
    cfg = db.query(LLMConfig).first()
    if cfg:
        cfg.api_endpoint = body.api_endpoint
        cfg.api_key_encrypted = encrypt(body.api_key)
        cfg.model = body.model
    else:
        cfg = LLMConfig(
            api_endpoint=body.api_endpoint,
            api_key_encrypted=encrypt(body.api_key),
            model=body.model,
        )
        db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.get("/config/key")
def get_decrypted_key(db: Session = Depends(get_db)):
    """Internal helper — returns decrypted key for agents."""
    cfg = db.query(LLMConfig).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="LLM config not set")
    return {"api_key": decrypt(cfg.api_key_encrypted)}
