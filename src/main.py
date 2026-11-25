# Carrega variáveis do arquivo .env mais próximo (pasta do projeto)
def _carregar_env():
    from pathlib import Path
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for pasta in Path(__file__).resolve().parents:
        if (pasta / ".env").exists():
            load_dotenv(pasta / ".env")
            break


_carregar_env()

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import load_config
from src.controllers.health_check_controller import health_route
from src.controllers.juridico_controller import juridico_route
from src.services.core.errors import GatewayError

# Carrega variables.DSV/secrets.DSV no ambiente local (no publicado, a pipeline já
# definiu as variáveis e override=False as preserva). Deve rodar ANTES de ler qualquer
# env var abaixo (ex.: get_allowed_origins na criação do middleware).
load_config()


def get_allowed_origins() -> list[str]:
    """Origins de CORS a partir de ALLOWED_ORIGINS (lista separada por vírgula).

    L5: CORS restrito — nunca combinar "*" com credenciais. Por padrão, lista vazia.
    """
    raw = os.getenv("ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="Hub BFF Comparador de Contratos Jurídico",
    description="BFF gateway dos microserviços GenAI da Gateway para o agente jurídico.",
    version="0.1.0",
    root_path="/api-comparador-contratos-juridico",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(GatewayError)
async def _gateway_error_handler(request: Request, exc: GatewayError):
    """L3/L6: exceção tipada → HTTP. Detalhe só no log; cliente recebe msg genérica."""
    return JSONResponse(status_code=exc.status_code, content={"message": exc.client_message})


app.include_router(health_route)
app.include_router(juridico_route)
