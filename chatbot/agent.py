"""
Agente conversacional do Cidade Conectada usando LangGraph.

Implementa o orquestrador de conversa com:
- Multi-turn conversation com contexto mantido
- Tool calls para consulta ao backend
- Extração de entidades para pré-preenchimento do formulário
- Detecção de intenção e fallback
"""

import logging
import os
import re
from typing import Annotated, Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from chatbot.prompts import FALLBACK_MESSAGE, LLM_UNAVAILABLE_MESSAGE, SYSTEM_PROMPT
from chatbot.tools import TOOLS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estado do grafo
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    user_token: str
    intent: str
    entities: dict[str, Any]


# ---------------------------------------------------------------------------
# Inicialização do LLM
# ---------------------------------------------------------------------------

def _build_llm() -> ChatGroq:
    """Inicializa o modelo Groq com as tools disponíveis."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY não configurada. Verifique o arquivo .env")

    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        groq_api_key=api_key,
        temperature=0.3,  # Respostas mais consistentes para atendimento
    )
    return llm.bind_tools(TOOLS)


# ---------------------------------------------------------------------------
# Nós do grafo
# ---------------------------------------------------------------------------

def call_llm(state: AgentState) -> dict:
    """
    Nó principal: chama o LLM com o histórico completo da conversa.
    Injeta o system prompt e o contexto do usuário.
    """
    llm = _build_llm()

    # Monta o contexto do usuário para injetar no system prompt
    user_context = f"\n\nContexto atual: userId={state['user_id']}"
    system_message = SystemMessage(content=SYSTEM_PROMPT + user_context)

    messages_with_system = [system_message] + state["messages"]

    try:
        response = llm.invoke(messages_with_system)
        return {"messages": [response]}
    except Exception as e:
        logger.exception("Erro ao chamar o LLM: %s", e)
        fallback = AIMessage(content=LLM_UNAVAILABLE_MESSAGE)
        return {"messages": [fallback]}


def extract_intent_and_entities(state: AgentState) -> dict:
    """
    Nó de pós-processamento: analisa a última mensagem do LLM para detectar
    intenção e extrair entidades estruturadas para o formulário de reporte.
    """
    last_message = state["messages"][-1]

    if not isinstance(last_message, AIMessage):
        return {"intent": "unknown", "entities": {}}

    content = last_message.content.lower() if isinstance(last_message.content, str) else ""

    # Detecção de intenção baseada no conteúdo da resposta
    intent = "faq"  # padrão

    if any(kw in content for kw in ["formulário", "pré-preenchido", "vou te redirecionar", "rua ", "avenida ", "localização"]):
        intent = "report"
    elif any(kw in content for kw in ["chamado #", "status:", "criado em:", "seus chamados"]):
        intent = "query_report"
    elif any(kw in content for kw in ["não entendi", "não consegui entender", "pode me ajudar com"]):
        intent = "unknown"

    # Extração de entidades quando a intenção é reporte
    entities: dict[str, Any] = {}
    if intent == "report":
        entities = _extract_report_entities(state["messages"])

    return {"intent": intent, "entities": entities}


def _extract_report_entities(messages: list[BaseMessage]) -> dict[str, Any]:
    """
    Extrai entidades de reporte (localização, descrição, categoria)
    do histórico de mensagens da conversa.
    """
    entities: dict[str, Any] = {}
    full_conversation = " ".join(
        m.content for m in messages
        if isinstance(m, (HumanMessage, AIMessage)) and isinstance(m.content, str)
    ).lower()

    # Extração de categoria por palavras-chave
    category_keywords = {
        "Pavimentação": ["buraco", "asfalto", "calçada", "pavimento", "cratera"],
        "Iluminação Pública": ["luz", "poste", "iluminação", "lâmpada", "escuro"],
        "Limpeza Urbana": ["lixo", "sujeira", "entulho", "coleta", "resíduos"],
        "Saneamento": ["bueiro", "esgoto", "entupido", "vazamento", "água"],
        "Arborização": ["árvore", "galho", "raiz", "poda", "planta"],
    }

    for category, keywords in category_keywords.items():
        if any(kw in full_conversation for kw in keywords):
            entities["category"] = category
            break

    if "category" not in entities:
        entities["category"] = "Outros"

    # Extração básica de localização por padrões comuns
    location_patterns = [
        r"rua\s+[\w\s]+",
        r"avenida\s+[\w\s]+",
        r"av\.\s+[\w\s]+",
        r"alameda\s+[\w\s]+",
        r"praça\s+[\w\s]+",
        r"bairro\s+[\w\s]+",
    ]

    for message in messages:
        if isinstance(message, HumanMessage) and isinstance(message.content, str):
            for pattern in location_patterns:
                match = re.search(pattern, message.content, re.IGNORECASE)
                if match:
                    entities["location"] = match.group(0).strip()[:100]
                    break
        if "location" in entities:
            break

    # A descrição é composta pelas mensagens do usuário
    user_messages = [
        m.content for m in messages
        if isinstance(m, HumanMessage) and isinstance(m.content, str)
    ]
    if user_messages:
        entities["description"] = user_messages[-1][:300]  # Última mensagem do usuário

    return entities


def should_use_tools(state: AgentState) -> str:
    """
    Decide o próximo nó do grafo:
    - Se o LLM pediu tool calls → vai para o nó de tools
    - Caso contrário → vai para extração de intenção
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "extract"


# ---------------------------------------------------------------------------
# Construção do grafo
# ---------------------------------------------------------------------------

def build_graph() -> Any:
    """Constrói e compila o grafo LangGraph do agente."""

    tool_node = ToolNode(TOOLS)

    graph = StateGraph(AgentState)

    # Adiciona os nós
    graph.add_node("llm", call_llm)
    graph.add_node("tools", tool_node)
    graph.add_node("extract", extract_intent_and_entities)

    # Define o nó de entrada
    graph.set_entry_point("llm")

    # Roteamento condicional após o LLM
    graph.add_conditional_edges(
        "llm",
        should_use_tools,
        {
            "tools": "tools",
            "extract": "extract",
        },
    )

    # Após executar tools, volta para o LLM para formular a resposta final
    graph.add_edge("tools", "llm")

    # Após extrair intenção e entidades, termina
    graph.add_edge("extract", END)

    return graph.compile()


# Instância compilada do grafo (singleton)
_graph = None


def get_graph() -> Any:
    """Retorna o grafo compilado, criando-o se necessário."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Função principal de invocação
# ---------------------------------------------------------------------------

def run_agent(
    user_id: str,
    user_token: str,
    messages: list[dict],
) -> dict[str, Any]:
    """
    Executa o agente com o histórico de mensagens fornecido.

    Args:
        user_id: ID do usuário autenticado
        user_token: Token de autenticação
        messages: Lista de mensagens no formato [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        Dicionário com message, intent, entities e action
    """
    # Converte as mensagens do formato da API para o formato LangChain
    lc_messages: list[BaseMessage] = []
    for msg in messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_messages.append(AIMessage(content=msg["content"]))

    initial_state: AgentState = {
        "messages": lc_messages,
        "user_id": user_id,
        "user_token": user_token,
        "intent": "faq",
        "entities": {},
    }

    graph = get_graph()

    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        logger.exception("Erro ao executar o agente: %s", e)
        return {
            "message": LLM_UNAVAILABLE_MESSAGE,
            "intent": "unknown",
            "entities": None,
            "action": {"type": "none"},
        }

    # Extrai a última mensagem do assistente
    response_message = ""
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage) and isinstance(msg.content, str) and msg.content:
            response_message = msg.content
            break

    if not response_message:
        response_message = FALLBACK_MESSAGE

    intent = final_state.get("intent", "faq")
    entities = final_state.get("entities", {})

    # Define a ação com base na intenção
    action: dict[str, Any] = {"type": "none"}
    if intent == "report" and entities:
        action = {
            "type": "navigate_to_form",
            "payload": {
                "location": entities.get("location"),
                "description": entities.get("description"),
                "category": entities.get("category"),
            },
        }

    return {
        "message": response_message,
        "intent": intent,
        "entities": entities if entities else None,
        "action": action,
    }
