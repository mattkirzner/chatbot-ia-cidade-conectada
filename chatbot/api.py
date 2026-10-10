"""
API FastAPI do Chatbot de IA — Cidade Conectada.
Expõe o endpoint POST /chat conforme especificado no design.md.
"""

import logging
import time
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from chatbot.agent import run_agent
from chatbot.prompts import SESSION_EXPIRED_MESSAGE

# Carrega variáveis de ambiente do .env
load_dotenv()

# Configuração de logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Modelos de dados (Pydantic)
# ---------------------------------------------------------------------------


class ChatMessageInput(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    userId: str = Field(..., min_length=1)
    conversationId: str = Field(..., min_length=1)
    messages: list[ChatMessageInput] = Field(..., min_length=1)


class ReportEntities(BaseModel):
    location: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class ChatAction(BaseModel):
    type: Literal["navigate_to_form", "none"]
    payload: Optional[ReportEntities] = None


class ChatResponse(BaseModel):
    message: str
    intent: Literal["faq", "report", "query_report", "unknown"]
    entities: Optional[ReportEntities] = None
    action: ChatAction


# ---------------------------------------------------------------------------
# Aplicação FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Chatbot de IA — Cidade Conectada",
    description="API do módulo de chatbot para o app Cidade Conectada",
    version="1.0.0",
)

# CORS — permite chamadas do app React Native e ferramentas de teste
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restringir em produção ao domínio do app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware de logging
# ---------------------------------------------------------------------------


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registra logs estruturados de cada requisição."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000)

    logger.info(
        "method=%s path=%s status=%s duration_ms=%d",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health_check():
    """Endpoint de health check para o Docker e monitoramento."""
    return {"status": "ok", "service": "chatbot-cidade-conectada"}


@app.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Processa uma mensagem do usuário e retorna a resposta do chatbot.

    - Mantém o contexto da conversa via histórico de mensagens
    - Consulta o backend do Cidade Conectada via tool calls quando necessário
    - Retorna intenção detectada e entidades extraídas para ações no app
    """
    # Valida o token de autenticação

    # versão a ser usada com o back-end rodando
    # if not authorization or not authorization.startswith("Bearer "):
    #     logger.warning(
    #         "Requisição sem token | conversationId=%s", body.conversationId
    #     )
    #     raise HTTPException(status_code=401, detail=SESSION_EXPIRED_MESSAGE)

    # user_token = authorization.removeprefix("Bearer ").strip()
    # if not user_token:
    #     raise HTTPException(status_code=401, detail=SESSION_EXPIRED_MESSAGE)

    # versão a ser usada sem back-end
    # Token opcional — usa "anonymous" se não fornecido (modo de desenvolvimento)
    user_token = "anonymous"
    if authorization and authorization.startswith("Bearer "):
        user_token = authorization.removeprefix("Bearer ").strip() or "anonymous"

    logger.info(
        "Chat request | conversationId=%s | userId=%s | messages=%d",
        body.conversationId,
        body.userId,
        len(body.messages),
    )

    # Converte para o formato esperado pelo agente
    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    # Executa o agente
    result = run_agent(
        user_id=body.userId,
        user_token=user_token,
        messages=messages,
    )

    logger.info(
        "Chat response | conversationId=%s | intent=%s",
        body.conversationId,
        result.get("intent"),
    )

    # Monta a resposta tipada
    entities = None
    if result.get("entities"):
        entities = ReportEntities(**result["entities"])

    action_data = result.get("action", {"type": "none"})
    action = ChatAction(
        type=action_data.get("type", "none"),
        payload=(
            ReportEntities(**action_data["payload"])
            if action_data.get("payload")
            else None
        ),
    )

    return ChatResponse(
        message=result["message"],
        intent=result.get("intent", "faq"),
        entities=entities,
        action=action,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captura erros não tratados e retorna resposta segura ao cliente."""
    logger.exception("Erro não tratado: %s", exc)
    return JSONResponse(
        status_code=503,
        content={
            "message": "O assistente está temporariamente indisponível. Por favor, use o app diretamente.",
            "intent": "unknown",
            "entities": None,
            "action": {"type": "none"},
        },
    )
