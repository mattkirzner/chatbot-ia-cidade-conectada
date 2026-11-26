"""
Três chamadas das funções de acesso, sem Groq e sem o app.

Uso, na pasta chatbot-ia-cidade-conectada:
    python -m chatbot.demonstrar
"""

from chatbot.dados import (
    buscar_ocorrencia,
    listar_ocorrencias_do_cidadao,
    sugerir_categoria,
)
from chatbot.log_uso import chamador


def _chamar(nome: str, acao):
    token = chamador.set("demonstrar")
    try:
        return acao()
    finally:
        chamador.reset(token)


def main() -> None:
    ana = _chamar("listar", lambda: listar_ocorrencias_do_cidadao("cidadao-ana"))
    print(f"1) listar_ocorrencias_do_cidadao('cidadao-ana') -> {len(ana)} registro(s)")
    for item in ana:
        print(
            f"   #{item.get('id_denuncia')} {item.get('titulo')} "
            f"| {item.get('status')}"
        )

    inexistente = _chamar("buscar", lambda: buscar_ocorrencia("99999"))
    print("2) buscar_ocorrencia('99999') ->", "não encontrada" if inexistente is None else inexistente)

    categoria = _chamar(
        "sugerir",
        lambda: sugerir_categoria("Poste de luz apagado na esquina"),
    )
    print("3) sugerir_categoria('Poste de luz apagado na esquina') ->", categoria)
    print("Log gravado em chatbot/data/uso_dados.jsonl")


if __name__ == "__main__":
    main()
