"""Contratos de saída (Pydantic) — L4: response tipado em todo endpoint.

Espelha o JSON do catálogo do fluxo Original vs Modificado (modifications[] + summary).
Se a Gateway devolver chaves diferentes, mapear no service antes de instanciar.
"""

from typing import Literal

from pydantic import BaseModel


class ModificationItem(BaseModel):
    type: Literal["adicao", "remocao", "alteracao"]
    original_text: str = ""
    modified_text: str = ""
    impact: str = ""
    risk_level: Literal["alto", "medio", "baixo"] = "baixo"
    suggestion: str = ""
    context: str = ""
    peso: Literal["alto", "medio", "baixo"] = "baixo"


class Summary(BaseModel):
    total_modifications: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    overall_risk: Literal["alto", "medio", "baixo"] = "baixo"


class ComparacaoVersoesResponse(BaseModel):
    id: str | None = None
    modifications: list[ModificationItem] = []
    summary: Summary = Summary()


class ChatResponse(BaseModel):
    resposta: str
    id_contexto: str | None = None


class AnalisePadraoOuroResponse(BaseModel):
    id: str | None = None
    analise_markdown: str
    indice_utilizado: str = ""
