# backend/routes/pagos.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
import models.models as models

router = APIRouter(prefix="/pagos", tags=["Pagos"])

# ====================================================
# 🔍 Ver pagos realizados
# ====================================================
@router.get("/")
def listar_pagos(db: Session = Depends(get_db)):
    pagos = db.query(models.Pago).all()
    return pagos
