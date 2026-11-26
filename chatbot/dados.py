"""
Funções de acesso aos dados mockados do módulo de IA.

Somente este arquivo abre ocorrencias.json. Ferramentas e rotas não leem o JSON direto.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from chatbot.log_uso import registrar_uso

DADOS_PATH = Path(__file__).resolve().parent / "data" / "ocorrencias.json"

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ILUMINACAO_PUBLICA": ("poste", "luz", "lâmpada", "lampada", "iluminação", "iluminacao", "escuro"),
    "MANUTENCAO_DE_VIAS": ("buraco", "asfalto", "calçada", "calcada", "via", "cratera"),
    "COLETA_DE_LIXO": ("lixo", "entulho", "coleta", "resíduo", "residuo", "saco"),
    "SANEAMENTO": ("bueiro", "esgoto", "vazamento", "água", "agua", "entupido"),
    "SINALIZACAO_DE_TRANSITO": ("placa", "semáforo", "semaforo", "faixa", "sinalização", "sinalizacao"),
    "SEGURANCA": ("assalto", "inseguro", "perigoso", "segurança", "seguranca"),
    "FISCALIZACAO": ("obra irregular", "sem autorização", "sem autorizacao", "fiscalização", "fiscalizacao"),
}


def _carregar() -> list[dict[str, Any]]:
    with DADOS_PATH.open(encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    if not isinstance(dados, list):
        return []
    return [item for item in dados if isinstance(item, dict)]


def listar_ocorrencias_do_cidadao(cidadao_id: str) -> list[dict[str, Any]]:
    """Devolve as ocorrências do cidadão de teste, ou lista vazia."""
    try:
        itens = [
            item
            for item in _carregar()
            if str(item.get("cidadao_id")) == str(cidadao_id)
        ]
        registrar_uso(
            "listar_ocorrencias_do_cidadao",
            {"cidadao_id": cidadao_id},
            len(itens),
            True,
        )
        return itens
    except Exception:
        registrar_uso(
            "listar_ocorrencias_do_cidadao",
            {"cidadao_id": cidadao_id},
            0,
            False,
        )
        raise


def buscar_ocorrencia(ocorrencia_id: str) -> Optional[dict[str, Any]]:
    """Devolve a ocorrência pelo número, ou None se não existir."""
    try:
        alvo = str(ocorrencia_id)
        encontrado = next(
            (
                item
                for item in _carregar()
                if str(item.get("id_denuncia")) == alvo
            ),
            None,
        )
        registrar_uso(
            "buscar_ocorrencia",
            {"ocorrencia_id": alvo},
            1 if encontrado else 0,
            encontrado is not None,
        )
        return encontrado
    except Exception:
        registrar_uso(
            "buscar_ocorrencia",
            {"ocorrencia_id": str(ocorrencia_id)},
            0,
            False,
        )
        raise


def sugerir_categoria(descricao: str) -> str:
    """
    Sugere uma categoria do SmartCitys com uma regra simples sobre a descrição.
    Sem correspondência, devolve OUTROS_EMPECILHOS.
    """
    texto = (descricao or "").casefold()
    recorte = texto[:80]
    try:
        categoria = "OUTROS_EMPECILHOS"
        for codigo, palavras in CATEGORY_KEYWORDS.items():
            if any(palavra in texto for palavra in palavras):
                categoria = codigo
                break
        registrar_uso(
            "sugerir_categoria",
            {"descricao": recorte},
            1,
            True,
        )
        return categoria
    except Exception:
        registrar_uso(
            "sugerir_categoria",
            {"descricao": recorte},
            0,
            False,
        )
        raise
