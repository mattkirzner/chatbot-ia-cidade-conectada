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
from typing import Annotated, Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from chatbot.prompts import EXTRACT_PROMPT, FALLBACK_MESSAGE, LLM_UNAVAILABLE_MESSAGE, SYSTEM_PROMPT
from chatbot.schema import ChatDecision, build_action, normalize_draft
from chatbot.tools import TOOLS, user_id as user_id_context, user_token as user_token_context

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


def _transcript(messages: list[BaseMessage]) -> str:
    lines: list[str] = []
    for message in messages:
        if isinstance(message, HumanMessage) and isinstance(message.content, str):
            lines.append(f"Usuário: {message.content}")
        elif (
            isinstance(message, AIMessage)
            and isinstance(message.content, str)
            and message.content
            and not message.tool_calls
        ):
            lines.append(f"Assistente: {message.content}")
    return "\n".join(lines)


def _structured_decision(messages: list[BaseMessage]) -> dict[str, Any]:
    """Pede ao modelo um objeto tipado, sem interpretar palavras-chave no texto."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY não configurada. Verifique o arquivo .env")

    structured = ChatGroq(
        model="openai/gpt-oss-20b",
        groq_api_key=api_key,
        temperature=0,
    ).with_structured_output(ChatDecision)

    result = structured.invoke([
        SystemMessage(content=EXTRACT_PROMPT),
        HumanMessage(content=_transcript(messages) or "Sem mensagens."),
    ])
    if isinstance(result, ChatDecision):
        payload = result.model_dump()
    elif isinstance(result, dict):
        payload = result
    else:
        raise TypeError("A classificação estruturada não retornou um objeto.")

    intent = payload.get("intent")
    if intent not in ("faq", "report", "query_report", "unknown"):
        intent = "unknown"
    return {"intent": intent, "entities": normalize_draft(payload.get("draft"))}


def extract_intent_and_entities(state: AgentState) -> dict:
    """Classifica a conversa e monta o rascunho com os enums do SmartCitys."""
    last_message = state["messages"][-1]
    if (
        isinstance(last_message, AIMessage)
        and last_message.content == LLM_UNAVAILABLE_MESSAGE
    ):
        return {"intent": "unknown", "entities": {}}

    try:
        return _structured_decision(state["messages"])
    except Exception as error:
        logger.exception("Erro ao classificar a conversa: %s", error)
        return {"intent": "unknown", "entities": {}}


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
    token_reset = user_token_context.set(user_token)
    user_reset = user_id_context.set(user_id)
    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        logger.exception("Erro ao executar o agente: %s", e)
        return {
            "message": LLM_UNAVAILABLE_MESSAGE,
            "intent": "unknown",
            "draft": None,
            "action": {"type": "none", "payload": None},
        }
    finally:
        user_token_context.reset(token_reset)
        user_id_context.reset(user_reset)

    # Extrai a última mensagem do assistente
    response_message = ""
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage) and isinstance(msg.content, str) and msg.content:
            response_message = msg.content
            break

    if not response_message:
        response_message = FALLBACK_MESSAGE

    intent = final_state.get("intent", "faq")
    draft = normalize_draft(final_state.get("entities"))
    action = build_action(intent, draft)

    return {
        "message": response_message,
        "intent": intent,
        "draft": draft,
        "action": action,
    }
