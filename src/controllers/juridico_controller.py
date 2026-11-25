from typing import Literal
"""Rotas do agente jurídico.

Valida entrada/saída (Pydantic, L4), expõe connection_mode como Query e delega ao
service. Services usam requests (síncrono) → chamados via run_in_threadpool para não
travar o event loop.
"""

from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.models.requests import ChatRequest
from src.models.responses import (
    AnalisePadraoOuroResponse,
    ComparacaoVersoesResponse,
    ChatResponse,
)
from src.services.juridico_service import (
    comparar_versoes_service,
    comparar_padrao_ouro_service,
    chat_analise_service,
)
from src.services.persistence_service import get_analysis

juridico_route = APIRouter()


@juridico_route.post(
    "/comparar/versoes",
    tags=["Jurídico"],
    response_model=ComparacaoVersoesResponse,
)
async def comparar_versoes(
    original: UploadFile = File(...),
    modificado: UploadFile = File(...),
    connection_mode: Literal["APIM", "GATEWAY"] = Query("APIM"),
):
    return await run_in_threadpool(
        comparar_versoes_service,
        await original.read(), original.filename,
        await modificado.read(), modificado.filename,
        connection_mode,
    )


@juridico_route.post(
    "/comparar/padrao-ouro",
    tags=["Jurídico"],
    response_model=AnalisePadraoOuroResponse,
)
async def comparar_padrao_ouro(
    padrao_ouro: UploadFile = File(...),
    contratada: UploadFile = File(...),
    connection_mode: Literal["APIM", "GATEWAY"] = Query("APIM"),
):
    return await run_in_threadpool(
        comparar_padrao_ouro_service,
        await padrao_ouro.read(), padrao_ouro.filename,
        await contratada.read(), contratada.filename,
        connection_mode,
    )


@juridico_route.post(
    "/chat/analise",
    tags=["Jurídico"],
    response_model=ChatResponse,
)
async def chat_analise(
    body: ChatRequest,
    connection_mode: Literal["APIM", "GATEWAY"] = Query("APIM"),
):
    return await run_in_threadpool(
        chat_analise_service,
        body.pergunta,
        body.id_contexto,
        connection_mode,
    )


@juridico_route.get("/analises/{analysis_id}", tags=["Jurídico"])
async def obter_analise(analysis_id: str):
    analysis = await run_in_threadpool(get_analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Análise não encontrada.")
    return analysis
