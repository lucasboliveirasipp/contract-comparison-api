"""Carregamento de configuração por arquivo (.DSV/.env) para desenvolvimento local.

No ambiente publicado, as variáveis vêm da pipeline/Key Vault (L12) e JÁ estão no
ambiente — por isso usamos override=False: o que já está definido VENCE o arquivo.
Localmente, basta preencher variables.DSV/secrets.DSV que o app passa a enxergá-las.

Ordem de carga: variables.DSV → secrets.DSV → .env (o primeiro a definir uma chave
vence, já que override=False).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_DEFAULT_FILES = ("variables.DSV", "secrets.DSV", ".env")


def load_config(root=None, files=_DEFAULT_FILES) -> list[str]:
    """Carrega variáveis de ambiente dos arquivos existentes em `root`.

    Args:
        root: diretório base. Se None, usa a raiz do projeto (pai de src/).
        files: nomes dos arquivos a tentar carregar, em ordem de prioridade.

    Returns:
        Lista dos arquivos efetivamente carregados (os que existiam).
    """
    base = Path(root) if root is not None else Path(__file__).resolve().parent.parent
    loaded: list[str] = []
    for name in files:
        path = base / name
        if path.exists():
            load_dotenv(path, override=False)
            loaded.append(name)
    return loaded
