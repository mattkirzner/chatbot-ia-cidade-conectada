"""
Ferramentas do agente.

Por padrão leem o JSON mockado (AV2). Com DATA_SOURCE=http consultam o gateway local.
"""

import logging
import os
from contextvars import ContextVar

import httpx
from langchain_core.tools import tool

from chatbot.dados import (
    buscar_ocorrencia,
    listar_ocorrencias_do_cidadao,
    sugerir_categoria,
)
from chatbot.log_uso import chamador

logger = logging.getLogger(__name__)

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
user_token: ContextVar[str] = ContextVar("user_token", default="")
user_id: ContextVar[str] = ContextVar("user_id", default="")

STATUS_LABELS = {
    "ABERTA": "Aberta",
    "EM_ANALISE": "Em análise",
    "RESOLVIDA": "Resolvida",
}

CATEGORY_LABELS = {
    "ILUMINACAO_PUBLICA": "Iluminação pública",
    "MANUTENCAO_DE_VIAS": "Manutenção de vias",
    "SANEAMENTO": "Saneamento",
    "COLETA_DE_LIXO": "Coleta de lixo",
    "FISCALIZACAO": "Fiscalização",
    "SEGURANCA": "Segurança",
    "SINALIZACAO_DE_TRANSITO": "Sinalização de trânsito",
    "OUTROS_EMPECILHOS": "Outros",
}


def _uses_http() -> bool:
    return os.getenv("DATA_SOURCE", "mock").strip().lower() == "http"


def _label(mapping: dict[str, str], value: object) -> str:
    if value is None:
        return "Não informado"
    return mapping.get(str(value), str(value))


def _missing_token_message() -> str | None:
    token = user_token.get().strip()
    if token and token != "anonymous":
        return None
    return "Sua sessão expirou. Faça login novamente no app para eu consultar suas ocorrências."


def _headers() -> dict[str, str]:
    token = user_token.get().strip()
    headers = {"Accept": "application/json"}
    if token and token != "anonymous":
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(path: str, params: dict | None = None) -> httpx.Response:
    with httpx.Client(timeout=8.0) as client:
        return client.get(
            f"{BACKEND_BASE_URL}{path}",
            params=params,
            headers=_headers(),
        )


def _format_occurrence(item: dict) -> str:
    description = str(item.get("descricao") or "Sem descrição")
    return (
        f"• Ocorrência #{item.get('id_denuncia', '?')} — {item.get('titulo') or description[:60]} "
        f"| {_label(CATEGORY_LABELS, item.get('categoria'))} "
        f"| Status: {_label(STATUS_LABELS, item.get('status'))}"
    )


def _list_from_mock() -> str:
    cidadao = user_id.get().strip() or "cidadao-sem-historico"
    token_reset = chamador.set("list_my_occurrences")
    try:
        items = listar_ocorrencias_do_cidadao(cidadao)
    finally:
        chamador.reset(token_reset)
    if not items:
        return "Você ainda não possui nenhuma ocorrência registrada no app."
    lines = ["Aqui estão suas ocorrências:\n"]
    lines.extend(_format_occurrence(item) for item in items)
    return "\n".join(lines)


def _get_from_mock(occurrence_id: str) -> str:
    token_reset = chamador.set("get_occurrence")
    try:
        item = buscar_ocorrencia(occurrence_id)
    finally:
        chamador.reset(token_reset)
    if not item:
        return f"Ocorrência #{occurrence_id} não encontrada."
    return (
        f"Ocorrência #{item.get('id_denuncia')}\n"
        f"Título: {item.get('titulo') or 'Não informado'}\n"
        f"Descrição: {item.get('descricao') or 'Não informada'}\n"
        f"Categoria: {_label(CATEGORY_LABELS, item.get('categoria'))}\n"
        f"Endereço: {item.get('endereco') or 'Não informado'}\n"
        f"Status: {_label(STATUS_LABELS, item.get('status'))}\n"
        f"Registrada em: {item.get('data_registro') or 'Não informado'}"
    )


def _list_from_http() -> str:
    missing_token = _missing_token_message()
    if missing_token:
        return missing_token
    try:
        page = 1
        items: list[dict] = []
        while page <= 20:
            response = _get("/demands/my-demands", {"page": page, "limit": 100})
            if response.status_code == 401:
                return "Sua sessão expirou. Faça login novamente no app para eu consultar suas ocorrências."
            response.raise_for_status()
            body = response.json()
            data = body.get("data", []) if isinstance(body, dict) else body
            items.extend(item for item in data if isinstance(item, dict))
            total_pages = 1
            if isinstance(body, dict):
                total_pages = int((body.get("pagination") or {}).get("totalPages") or 1)
            if page >= total_pages:
                break
            page += 1

        if not items:
            return "Você ainda não possui nenhuma ocorrência registrada no app."

        lines = ["Aqui estão suas ocorrências:\n"]
        lines.extend(_format_occurrence(item) for item in items)
        return "\n".join(lines)
    except httpx.TimeoutException:
        logger.warning("Timeout ao listar ocorrências locais")
        return "Não foi possível consultar suas ocorrências no momento. Tente novamente em instantes."
    except httpx.HTTPStatusError as error:
        logger.error("Erro HTTP ao listar ocorrências: %s", error.response.status_code)
        return "Não foi possível consultar suas ocorrências. Tente novamente mais tarde."
    except Exception as error:
        logger.exception("Erro inesperado ao listar ocorrências: %s", error)
        return "Ocorreu um erro ao consultar suas ocorrências."


def _get_from_http(occurrence_id: str) -> str:
    missing_token = _missing_token_message()
    if missing_token:
        return missing_token
    try:
        response = _get(f"/demands/{occurrence_id}")
        if response.status_code == 401:
            return "Sua sessão expirou. Faça login novamente no app para eu consultar essa ocorrência."
        if response.status_code in (403, 404):
            return f"Ocorrência #{occurrence_id} não encontrada."
        response.raise_for_status()
        item = response.json()
        if not isinstance(item, dict):
            return f"Ocorrência #{occurrence_id} não encontrada."
        return (
            f"Ocorrência #{item.get('id_denuncia')}\n"
            f"Título: {item.get('titulo') or 'Não informado'}\n"
            f"Descrição: {item.get('descricao') or 'Não informada'}\n"
            f"Categoria: {_label(CATEGORY_LABELS, item.get('categoria'))}\n"
            f"Endereço: {item.get('endereco') or 'Não informado'}\n"
            f"Status: {_label(STATUS_LABELS, item.get('status'))}\n"
            f"Registrada em: {item.get('data_registro') or 'Não informado'}"
        )
    except httpx.TimeoutException:
        logger.warning("Timeout ao buscar ocorrência %s", occurrence_id)
        return "Não foi possível consultar a ocorrência no momento. Tente novamente em instantes."
    except httpx.HTTPStatusError as error:
        logger.error("Erro HTTP ao buscar ocorrência %s: %s", occurrence_id, error.response.status_code)
        return "Não foi possível consultar a ocorrência. Tente novamente mais tarde."
    except Exception as error:
        logger.exception("Erro inesperado ao buscar ocorrência %s: %s", occurrence_id, error)
        return "Ocorreu um erro ao consultar a ocorrência."


@tool
def list_my_occurrences() -> str:
    """
    Lista as ocorrências do cidadão autenticado.
    Use quando a pessoa perguntar pelos próprios registros ou pelo status geral.
    """
    if _uses_http():
        return _list_from_http()
    return _list_from_mock()


@tool
def get_occurrence(occurrence_id: str) -> str:
    """
    Busca uma ocorrência própria pelo número.
    Use quando a pessoa informar o número de uma ocorrência específica.
    """
    if _uses_http():
        return _get_from_http(occurrence_id)
    return _get_from_mock(occurrence_id)


@tool
def suggest_category(descricao: str) -> str:
    """
    Sugere a categoria de um relato urbano a partir da descrição.
    Use quando a pessoa descrever um problema e ainda não tiver escolhido a categoria.
    """
    token_reset = chamador.set("suggest_category")
    try:
        categoria = sugerir_categoria(descricao)
    finally:
        chamador.reset(token_reset)
    return (
        f"Categoria sugerida: {_label(CATEGORY_LABELS, categoria)} "
        f"({categoria}). Confirme ou descreva outra."
    )


TOOLS = [list_my_occurrences, get_occurrence, suggest_category]
