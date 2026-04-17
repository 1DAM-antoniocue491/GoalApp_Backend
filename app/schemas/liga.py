"""
Schemas de validación para el recurso Liga.
Define los modelos Pydantic para request/response de la API relacionados con ligas de fútbol.
"""
from pydantic import BaseModel, Field
from datetime import datetime

class LigaBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    temporada: str = Field(..., max_length=20)
    categoria: str | None = Field(None, max_length=50)
    activa: bool = True

class LigaCreate(LigaBase):
    pass

class LigaUpdate(BaseModel):
    nombre: str | None = Field(None, max_length=100)
    temporada: str | None = Field(None, max_length=20)
    categoria: str | None = Field(None, max_length=50)
    activa: bool | None = None

class LigaResponse(BaseModel):
    id_liga: int
    nombre: str
    temporada: str
    categoria: str | None
    activa: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
