"""
Rascunho de ocorrência no contrato do SmartCitys.
A navegação para o formulário só acontece com os campos obrigatórios do OpenAPI.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

CATEGORIES = (
    "ILUMINACAO_PUBLICA",
    "MANUTENCAO_DE_VIAS",
    "SANEAMENTO",
    "COLETA_DE_LIXO",
    "FISCALIZACAO",
    "SEGURANCA",
    "SINALIZACAO_DE_TRANSITO",
    "OUTROS_EMPECILHOS",
)

REGIONS = (
    "REGIAO_METROPOLITANA_DO_RECIFE",
    "ZONA_DA_MATA",
    "AGRESTE",
    "SERTAO",
    "OUTRA",
)

PRIORITIES = ("ALTA", "MEDIA", "BAIXA")

INTENTS = ("faq", "report", "query_report", "unknown")

Category = Literal[
    "ILUMINACAO_PUBLICA",
    "MANUTENCAO_DE_VIAS",
    "SANEAMENTO",
    "COLETA_DE_LIXO",
    "FISCALIZACAO",
    "SEGURANCA",
    "SINALIZACAO_DE_TRANSITO",
    "OUTROS_EMPECILHOS",
]
Region = Literal[
    "REGIAO_METROPOLITANA_DO_RECIFE",
    "ZONA_DA_MATA",
    "AGRESTE",
    "SERTAO",
    "OUTRA",
]
Priority = Literal["ALTA", "MEDIA", "BAIXA"]
Intent = Literal["faq", "report", "query_report", "unknown"]

REQUIRED_DRAFT_FIELDS = ("titulo", "categoria", "regiao", "descricao")


class OccurrenceDraft(BaseModel):
    titulo: Optional[str] = None
    categoria: Optional[Category] = None
    regiao: Optional[Region] = None
    descricao: Optional[str] = None
    endereco: Optional[str] = None
    prioridade: Optional[Priority] = None


class ChatDecision(BaseModel):
    intent: Intent
    draft: OccurrenceDraft = Field(default_factory=OccurrenceDraft)


def _text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _choice(value: Any, allowed: tuple[str, ...]) -> Optional[str]:
    if isinstance(value, str) and value in allowed:
        return value
    return None


def normalize_draft(raw: dict[str, Any] | None) -> dict[str, Any]:
    source = raw or {}
    return {
        "titulo": _text(source.get("titulo")),
        "categoria": _choice(source.get("categoria"), CATEGORIES),
        "regiao": _choice(source.get("regiao"), REGIONS),
        "descricao": _text(source.get("descricao")),
        "endereco": _text(source.get("endereco")),
        "prioridade": _choice(source.get("prioridade"), PRIORITIES),
    }


def draft_is_ready(draft: dict[str, Any]) -> bool:
    return all(draft.get(field) for field in REQUIRED_DRAFT_FIELDS)


def build_action(intent: str, draft: dict[str, Any]) -> dict[str, Any]:
    if intent == "report" and draft_is_ready(draft):
        return {"type": "navigate_to_form", "payload": draft}
    return {"type": "none", "payload": None}
