"""
Tool calls para consulta ao backend do Cidade Conectada.
Todas as operações são somente leitura (GET).
"""

import logging
import os
from typing import Optional

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:3000")


def _get_headers(user_token: str) -> dict:
    """Retorna os headers de autenticação para chamadas ao backend."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }


@tool
def get_user_reports(user_id: str, user_token: str) -> str:
    """
    Busca todos os chamados abertos pelo usuário autenticado.
    Retorna uma lista formatada com id, descrição resumida e status de cada chamado.
    Use esta ferramenta quando o usuário perguntar sobre seus chamados em geral.

    Args:
        user_id: ID do usuário autenticado
        user_token: Token de autenticação do usuário
    """
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(
                f"{BACKEND_BASE_URL}/reports",
                params={"userId": user_id},
                headers=_get_headers(user_token),
            )
            response.raise_for_status()
            reports = response.json()

        if not reports:
            return "Você ainda não possui nenhum chamado registrado no app."

        lines = ["Aqui estão seus chamados:\n"]
        for r in reports:
            lines.append(
                f"• Chamado #{r.get('id', '?')} — {r.get('description', 'Sem descrição')[:60]} "
                f"| Status: {r.get('status', 'Desconhecido')}"
            )
        return "\n".join(lines)

    except httpx.TimeoutException:
        logger.warning("Timeout ao buscar chamados do usuário %s", user_id)
        return "Não foi possível consultar seus chamados no momento. Tente novamente em instantes."
    except httpx.HTTPStatusError as e:
        logger.error("Erro HTTP ao buscar chamados: %s", e.response.status_code)
        return "Não foi possível consultar seus chamados. Tente novamente mais tarde."
    except Exception as e:
        logger.exception("Erro inesperado ao buscar chamados: %s", e)
        return "Ocorreu um erro ao consultar seus chamados."


@tool
def get_report_by_id(report_id: str, user_id: str, user_token: str) -> str:
    """
    Busca os detalhes e status de um chamado específico pelo seu ID.
    Use esta ferramenta quando o usuário perguntar sobre um chamado específico pelo número.

    Args:
        report_id: ID/número do chamado a consultar
        user_id: ID do usuário autenticado (para validação de propriedade)
        user_token: Token de autenticação do usuário
    """
    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(
                f"{BACKEND_BASE_URL}/reports/{report_id}",
                headers=_get_headers(user_token),
            )

            # Chamado não encontrado ou não pertence ao usuário
            if response.status_code == 404:
                return f"Chamado #{report_id} não encontrado. Verifique o número e tente novamente."
            if response.status_code == 403:
                return f"Chamado #{report_id} não encontrado."  # Não revela que existe mas pertence a outro usuário

            response.raise_for_status()
            report = response.json()

        # Valida que o chamado pertence ao usuário autenticado
        if str(report.get("userId", "")) != str(user_id):
            return f"Chamado #{report_id} não encontrado."

        return (
            f"Chamado #{report.get('id')}\n"
            f"Descrição: {report.get('description', 'Não informada')}\n"
            f"Categoria: {report.get('category', 'Não informada')}\n"
            f"Localização: {report.get('location', 'Não informada')}\n"
            f"Status: {report.get('status', 'Desconhecido')}\n"
            f"Criado em: {report.get('createdAt', 'Não informado')}"
        )

    except httpx.TimeoutException:
        logger.warning("Timeout ao buscar chamado %s", report_id)
        return "Não foi possível consultar o chamado no momento. Tente novamente em instantes."
    except httpx.HTTPStatusError as e:
        logger.error("Erro HTTP ao buscar chamado %s: %s", report_id, e.response.status_code)
        return "Não foi possível consultar o chamado. Tente novamente mais tarde."
    except Exception as e:
        logger.exception("Erro inesperado ao buscar chamado %s: %s", report_id, e)
        return "Ocorreu um erro ao consultar o chamado."


# Lista de tools disponíveis para o agente
TOOLS = [get_user_reports, get_report_by_id]
