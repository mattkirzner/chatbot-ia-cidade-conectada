# Design — Módulo de Chatbot de IA
## Cidade Conectada

---

## 1. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    App Cidade Conectada                      │
│                      (React Native)                          │
│                                                              │
│   ┌──────────────┐     ┌───────────────┐                    │
│   │   Chat UI    │────▶│ Chat Service  │                    │
│   │  (ChatScreen)│     │ (chatService) │                    │
│   └──────────────┘     └───────┬───────┘                    │
│                                │                             │
│   ┌──────────────┐     ┌───────▼───────┐                    │
│   │  Formulário  │◀────│  Navigation   │                    │
│   │  de Reporte  │     │   (React Nav) │                    │
│   └──────────────┘     └───────────────┘                    │
│                                                              │
│   ┌──────────────────────────────────────┐                  │
│   │         Auth Context                  │                  │
│   │  (token do usuário autenticado)       │                  │
│   └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
              │                         │
              ▼                         ▼
┌─────────────────────┐    ┌────────────────────────┐
│   Chat API Gateway  │    │  Backend Cidade         │
│   (serviço próprio) │    │  Conectada (REST API)   │
│                     │    │  [somente leitura]       │
│  ┌───────────────┐  │    └────────────────────────┘
│  │  Orquestrador │  │
│  │  de Conversa  │  │
│  │  (LLM + Tools)│  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │   Extrator    │  │
│  │  de Entidades │  │
│  └───────────────┘  │
└─────────────────────┘
              │
              ▼
┌─────────────────────┐
│  Serviço de LLM     │
│  (OpenAI / Gemini)  │
│  [externo, HTTPS]   │
└─────────────────────┘
```

---

## 2. Fluxo dos Dados

### Fluxo 1 — Dúvida geral sobre o app

```
Usuário → Chat UI → chatService → Chat API Gateway → LLM
LLM → Chat API Gateway → chatService → Chat UI → Usuário
```

### Fluxo 2 — Abertura de chamado guiada

```
Usuário → Chat UI → chatService → Chat API Gateway → LLM (multi-turn)
LLM extrai entidades {localização, categoria, descrição}
Chat API Gateway → chatService → Navigation (com parâmetros preenchidos)
Navigation → Tela de Formulário (campos pré-preenchidos)
Usuário revisa e envia o formulário → Backend Cidade Conectada
```

### Fluxo 3 — Consulta de chamados

```
Usuário → Chat UI → chatService → Chat API Gateway
Orquestrador detecta intenção de consulta → tool call get_reports(user_id, report_id?)
Chat API Gateway → Backend Cidade Conectada (GET /reports?userId=X) [somente leitura]
Backend → Chat API Gateway → LLM (formata resposta em linguagem natural)
LLM → Chat API Gateway → chatService → Chat UI → Usuário
```

### Fluxo 4 — Fallback

```
Usuário → Chat UI → chatService → Chat API Gateway → LLM
LLM não reconhece intenção → retorna intent = "unknown"
Chat API Gateway → chatService → Chat UI (exibe mensagem de fallback + sugestões)
```

---

## 3. Modelo de Dados

### Mensagem de conversa (lado cliente)

```typescript
type MessageRole = 'user' | 'assistant';

interface ChatMessage {
  id: string;           // UUID local
  role: MessageRole;
  content: string;      // texto da mensagem
  timestamp: Date;
}
```

### Histórico de conversa enviado ao gateway

```typescript
interface ChatRequest {
  userId: string;               // ID do usuário autenticado
  conversationId: string;       // UUID da sessão de conversa
  messages: ChatMessage[];      // histórico completo da conversa
}
```

### Resposta do gateway

```typescript
interface ChatResponse {
  message: string;              // resposta em linguagem natural
  intent: ChatIntent;           // intenção detectada
  entities?: ReportEntities;    // dados extraídos (quando intent = 'report')
  action?: ChatAction;          // ação a executar no app
}

type ChatIntent = 'faq' | 'report' | 'query_report' | 'unknown';

interface ReportEntities {
  location?: string;
  description?: string;
  category?: string;
}

type ChatAction = 
  | { type: 'navigate_to_form'; payload: ReportEntities }
  | { type: 'none' };
```

---

## 4. Estratégia Principal e Baseline

### Estratégia principal

O módulo utiliza um LLM (Large Language Model) acessado via API externa como motor de linguagem natural. A estratégia é baseada em **prompt engineering com multi-turn conversation**:

- Um **system prompt** define o papel do chatbot, o tom de comunicação (simples, acessível, em português), as intenções suportadas e as instruções de fallback.
- O **histórico completo da conversa** é enviado a cada requisição para manter o contexto (stateless no backend, stateful no cliente).
- **Tool calls** são utilizados para consultas ao backend do Cidade Conectada, permitindo que o LLM decida quando buscar dados reais.

### Baseline

Na ausência de resposta do LLM (timeout ou erro), o sistema exibe uma mensagem de fallback estática predefinida, orientando o usuário a utilizar o app diretamente.

---

## 5. Interface de Integração

### Endpoint principal: `POST /chat`

**Descrição:** Processa uma mensagem do usuário e retorna a resposta do chatbot.

**Campos de entrada:**

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `userId` | string | Sim | ID do usuário autenticado no app |
| `conversationId` | string | Sim | UUID da sessão de conversa atual |
| `messages` | array | Sim | Histórico de mensagens da conversa (role + content) |
| `messages[].role` | string | Sim | `"user"` ou `"assistant"` |
| `messages[].content` | string | Sim | Texto da mensagem |

**Exemplo de requisição:**

```json
POST /chat
Authorization: Bearer <token_do_usuario>
Content-Type: application/json

{
  "userId": "usr_12345",
  "conversationId": "conv_abc-def-ghi",
  "messages": [
    {
      "role": "user",
      "content": "Quero reportar um buraco na Rua das Flores, perto do número 200"
    }
  ]
}
```

**Campos de saída:**

| Campo | Tipo | Descrição |
|---|---|---|
| `message` | string | Resposta do chatbot em linguagem natural |
| `intent` | string | Intenção detectada: `faq`, `report`, `query_report`, `unknown` |
| `entities` | object | Dados extraídos da conversa (presente quando `intent = "report"`) |
| `entities.location` | string | Localização extraída |
| `entities.description` | string | Descrição do problema |
| `entities.category` | string | Categoria sugerida |
| `action` | object | Ação a ser executada pelo app cliente |
| `action.type` | string | `navigate_to_form` ou `none` |
| `action.payload` | object | Dados para pré-preenchimento do formulário |

**Exemplo de resposta:**

```json
HTTP 200 OK
{
  "message": "Entendi! Você quer reportar um buraco na Rua das Flores próximo ao número 200. Vou te redirecionar para o formulário com as informações já preenchidas. Por favor, confirme os dados e envie o chamado.",
  "intent": "report",
  "entities": {
    "location": "Rua das Flores, próximo ao número 200",
    "description": "Buraco na via pública",
    "category": "Pavimentação"
  },
  "action": {
    "type": "navigate_to_form",
    "payload": {
      "location": "Rua das Flores, próximo ao número 200",
      "description": "Buraco na via pública",
      "category": "Pavimentação"
    }
  }
}
```

---

## 6. Tratamento de Erros e Estratégia de Contingência

| Código HTTP | Situação | Resposta ao usuário |
|---|---|---|
| 400 | Requisição malformada (campos obrigatórios ausentes) | Mensagem técnica de erro para log; chatbot não exibe ao usuário |
| 401 | Token de autenticação inválido ou expirado | Chatbot exibe: "Sua sessão expirou. Por favor, faça login novamente." |
| 503 | Serviço de LLM indisponível | Chatbot exibe: "O assistente está temporariamente indisponível. Por favor, use o app diretamente." |
| 504 | Timeout na chamada ao LLM (> 10 segundos) | Chatbot exibe: "Demorei para responder. Tente novamente em instantes." |

**Estratégia de contingência:**
- Todas as falhas são registradas em log no Chat API Gateway com `conversationId`, `userId` (anonimizado se possível) e código de erro.
- O cliente React Native exibe indicador visual de "digitando" enquanto aguarda resposta e remove o indicador em caso de erro.
- Não há retry automático no cliente — o usuário pode reenviar a mensagem manualmente.

---

## 7. Segurança, Privacidade e Observabilidade

### Segurança

- Todas as requisições ao Chat API Gateway exigem o token de autenticação do usuário (`Authorization: Bearer`), o mesmo utilizado nas demais chamadas ao backend do app.
- O `userId` extraído do token é usado para escopar todas as consultas ao backend — o servidor nunca aceita `userId` enviado no corpo da requisição sem validação contra o token.
- As mensagens enviadas ao serviço de LLM externo não devem conter dados sensíveis além do necessário (sem CPF, endereço completo, senhas, etc.).

### Privacidade

- O histórico de conversa é mantido apenas na memória do cliente (estado do componente React Native) durante a sessão. Não é persistido localmente nem no backend entre sessões.
- O envio de mensagens ao LLM externo deve ser coberto pela política de privacidade do app Cidade Conectada, informando ao usuário que o conteúdo pode ser processado por um serviço de terceiros.
- Nenhuma informação de localização real do dispositivo é coletada automaticamente — a localização é fornecida pelo usuário via texto na conversa.

### Observabilidade

- O Chat API Gateway registra logs estruturados para cada requisição: `timestamp`, `conversationId`, `intent` detectada, latência da chamada ao LLM e código de resposta HTTP.
- Métricas recomendadas para monitoramento: taxa de intenções `unknown` (indica qualidade do prompt), latência média do LLM, taxa de erros 503/504.
- `userId` nos logs deve ser tratado como dado sensível e, quando possível, armazenado de forma anonimizada ou pseudonimizada.
