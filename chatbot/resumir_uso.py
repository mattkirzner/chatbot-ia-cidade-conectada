"""
Resumo do log de uso dos dados mockados.

Uso, na pasta chatbot-ia-cidade-conectada:
    python -m chatbot.resumir_uso
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from chatbot.dados import DADOS_PATH
from chatbot.log_uso import LOG_PATH


def _linhas() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    registros: list[dict] = []
    for linha in LOG_PATH.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha:
            continue
        registros.append(json.loads(linha))
    return registros


def _ids_na_base() -> set[str]:
    dados = json.loads(DADOS_PATH.read_text(encoding="utf-8"))
    return {str(item.get("id_denuncia")) for item in dados if isinstance(item, dict)}


def main() -> None:
    linhas = _linhas()
    if not linhas:
        print("Ainda não há log. Rode: python -m chatbot.demonstrar")
        return

    por_funcao = Counter(item.get("funcao") for item in linhas)
    erros = [item for item in linhas if item.get("ok") is False]
    consultados: Counter[str] = Counter()
    for item in linhas:
        parametros = item.get("parametros") or {}
        if "ocorrencia_id" in parametros:
            consultados[str(parametros["ocorrencia_id"])] += 1
        if "cidadao_id" in parametros:
            consultados[f"cidadao:{parametros['cidadao_id']}"] += 1

    nunca = sorted(_ids_na_base() - {chave for chave in consultados if chave.isdigit()})

    print("Chamadas por função:")
    for nome, quantidade in por_funcao.most_common():
        print(f"  {nome}: {quantidade}")
    print(f"Erros (ok=false): {len(erros)}")
    print("Registros mais consultados:", consultados.most_common(5) or "nenhum")
    print("Ids da base nunca consultados pelo número:", nunca or "nenhum")

    mais_usado = consultados.most_common(1)
    if mais_usado:
        dado, vezes = mais_usado[0]
        resposta_a = (
            f"(a) O módulo mais usa {dado} ({vezes} vez(es) no log), "
            "junto com a listagem de cidadao-ana."
        )
    else:
        resposta_a = "(a) Ainda não há identificadores no log."

    if nunca:
        resposta_b = (
            f"(b) Os ids {', '.join(nunca)} nunca foram buscados pelo número. "
            "A ocorrência 205 (FISCALIZACAO, caso sem semelhantes) só aparece "
            "se alguém listar cidadao-bruno ou consultar esse id. "
            "Isso sugere dado difícil de alcançar nas três chamadas da demonstração."
        )
    else:
        resposta_b = "(b) Todos os ids da base foram consultados pelo número."

    if erros:
        motivos = [
            str((item.get("parametros") or {}).get("ocorrencia_id") or item.get("funcao"))
            for item in erros
        ]
        resposta_c = (
            f"(c) Houve {len(erros)} erro(s) esperado(s): {', '.join(motivos)}. "
            "O id 99999 não existe no JSON; a função devolve vazio e registra ok=false."
        )
    else:
        resposta_c = "(c) Não houve erro no log atual."

    print()
    print(resposta_a)
    print(resposta_b)
    print(resposta_c)


if __name__ == "__main__":
    main()
