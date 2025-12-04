# backend/routes/historial.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
import models.models as models

router = APIRouter(prefix="/historial", tags=["Historial de Estados"])

