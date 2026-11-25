"""Contratos de entrada (Pydantic) — L4: request tipado em todo endpoint."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    pergunta: str
    id_contexto: str | None = None
