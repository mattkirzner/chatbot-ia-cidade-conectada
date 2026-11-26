"""Registro simples do uso das funções de acesso aos dados mockados."""

from __future__ import annotations

import json
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
LOG_PATH = DATA_DIR / "uso_dados.jsonl"
chamador: ContextVar[str] = ContextVar("chamador", default="desconhecido")


def registrar_uso(
    funcao: str,
    parametros: dict[str, Any],
    registros: int,
    ok: bool,
) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    linha = {
        "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "funcao": funcao,
        "chamador": chamador.get(),
        "parametros": parametros,
        "registros": registros,
        "ok": ok,
    }
    with LOG_PATH.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(linha, ensure_ascii=False) + "\n")
