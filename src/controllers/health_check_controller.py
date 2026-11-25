from fastapi import APIRouter

health_route = APIRouter()


@health_route.get(
    "/health/liveness",
    name="Estado da aplicação",
    description="Utilizado pela esteira para validar o estado da aplicação",
    summary="Retorna o estado da aplicação para controle da esteira",
    tags=["Health"],
)
async def liveness():
    return {
        "title": "Estado da aplicação",
        "description": "Utilizado pela esteira para validar o estado da aplicação",
        "version": "v1.0",
        "status": "OK",
    }


@health_route.get(
    "/health/readiness",
    name="Status da prontidão",
    description="Utilizado pela esteira para validar a prontidão da aplicação",
    summary="Retorna a prontidão da aplicação para controle da esteira",
    tags=["Health"],
)
async def readiness():
    return {
        "title": "Status da prontidão",
        "description": "Utilizado pela esteira para validar a prontidão da aplicação",
        "version": "v1.0",
        "status": "OK",
    }
