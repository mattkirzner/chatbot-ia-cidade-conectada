# Chatbot de IA — Cidade Conectada

Módulo de chatbot de IA para o app Cidade Conectada. Permite que cidadãos tirem dúvidas sobre o app, reportem problemas de infraestrutura urbana e consultem o status de chamados, tudo via conversa em linguagem natural.

---

## Tecnologias utilizadas

| Tecnologia | Versão | Função |
|---|---|---|
| **Python** | 3.11 | Linguagem principal do módulo |
| **LangGraph** | 0.2.55 | Orquestração do agente conversacional (grafo de estados) |
| **LangChain Groq** | ≥0.2.0 | Integração com o modelo de linguagem via API do Groq |
| **Groq API** | — | Provedor do LLM (modelo `openai/gpt-oss-20b`), gratuito |
| **FastAPI** | 0.115.6 | Framework web para exposição do endpoint `POST /chat` |
| **Uvicorn** | 0.32.1 | Servidor ASGI para rodar o FastAPI |
| **Pydantic** | 2.10.4 | Validação e tipagem dos modelos de dados da API |
| **httpx** | 0.28.1 | Cliente HTTP para chamadas ao backend do Cidade Conectada |
| **python-dotenv** | 1.0.1 | Carregamento das variáveis de ambiente do arquivo `.env` |
| **Docker** + **Compose** | — | Empacotamento e execução do serviço em container |

---

## Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose instalados

---

## Como rodar

### 1. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Abra o arquivo `.env` e preencha sua chave de API do Groq:

```
GROQ_API_KEY=sua_chave_aqui
```

Obtenha sua chave gratuitamente em: https://console.groq.com/keys

### 2. Suba o container

```bash
docker compose up --build
```

A API estará disponível em: **http://localhost:8000**

### 3. Verifique se está rodando

```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{"status": "ok", "service": "chatbot-cidade-conectada"}
```

---

## Como testar o chatbot

> **Nota sobre histórico:** o backend é stateless. Para simular uma conversa com contexto, envie todas as mensagens anteriores no array `messages` a cada requisição.

---

### Caso 1 — Dúvida geral sobre o app

Simula um usuário que não sabe como usar o app. Espera-se `intent: faq`. (Está saindo `intent: report`, algo a ser corrigido no futuro)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"usr_123\", \"conversationId\": \"conv_001\", \"messages\": [{\"role\": \"user\", \"content\": \"Como eu faco para reportar um problema?\"}]}"
```

**Resultado esperado:**
```json
{
	"message": "Oi! Para reportar um problema de infraestrutura, basta me passar três informações simples:\n\n1. **Localização** – onde está o problema (rua, bairro, ponto de referência).\n2. **Descrição** – o que está acontecendo (ex.: “buraco grande na calçada”, “luz apagada na esquina”).\n3. **Categoria** – tipo do problema (pode sugerir, mas se não souber, eu ajudo a escolher).\n\nQuando eu tiver esses dados, confirmarei com você e te encaminharei ao formulário já com tudo preenchido para revisão e envio.  \nVamos começar? Por favor, me diga a localização do problema.",
	"intent": "report",
	"entities": {
		"location": null,
		"description": "Como eu faço para reportar um problema?",
		"category": "Pavimentação"
	},
	"action": {
		"type": "navigate_to_form",
		"payload": {
			"location": null,
			"description": "Como eu faço para reportar um problema?",
			"category": "Pavimentação"
		}
	}
}
```

---

### Caso 2 — Reporte de problema com localização

Simula um cidadão descrevendo um problema de infraestrutura. Espera-se `intent: report` e `action.type: navigate_to_form` com os campos extraídos.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"usr_123\", \"conversationId\": \"conv_002\", \"messages\": [{\"role\": \"user\", \"content\": \"Tem um buraco enorme na Rua das Flores perto do numero 200\"}]}"
```

**Resultado esperado:**
```json
{
	"message": "Claro! Vou preparar o relatório para você.\n\n**Localização**: Rua das Flores, perto do número 200  \n**Descrição**: Buraco enorme  \n**Categoria**: Pavimentação  \n\nTudo certo? Se estiver de acordo, eu vou redirecionar você para o formulário com esses dados já preenchidos, para que você possa revisar e enviar. É só confirmar!",
	"intent": "report",
	"entities": {
		"location": "Rua das Flores perto do numero 200",
		"description": "Tem um buraco enorme na Rua das Flores perto do numero 200",
		"category": "Pavimentação"
	},
	"action": {
		"type": "navigate_to_form",
		"payload": {
			"location": "Rua das Flores perto do numero 200",
			"description": "Tem um buraco enorme na Rua das Flores perto do numero 200",
			"category": "Pavimentação"
		}
	}
}
```

---

### Caso 3 — Consulta de status de chamado

Simula um usuário perguntando sobre um chamado existente. Espera-se `intent: query_report`. Como não há backend real conectado, o chatbot retorna a mensagem de indisponibilidade definida em `tools.py`.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"usr_123\", \"conversationId\": \"conv_003\", \"messages\": [{\"role\": \"user\", \"content\": \"Qual o status do meu chamado?\"}]}"
```

**Resultado esperado:**
```json
{
	"message": "Claro! Para eu conseguir verificar o status do seu chamado, preciso do seu token de autenticação. Você pode me enviar o token que recebeu ao fazer login no app? Assim eu consigo consultar os seus chamados e te informar o status atual.",
	"intent": "query_report",
	"entities": null,
	"action": {
		"type": "none",
		"payload": null
	}
}
```

---

### Caso 4 — Conversa multi-turn (contexto acumulado)

Simula uma conversa em dois turnos onde o usuário fornece a localização em mensagens separadas. Demonstra que o histórico é mantido pelo cliente.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"usr_123\", \"conversationId\": \"conv_004\", \"messages\": [{\"role\": \"user\", \"content\": \"Tem um buraco na rua\"}, {\"role\": \"assistant\", \"content\": \"Entendi! Pode me informar a localizacao exata?\"}, {\"role\": \"user\", \"content\": \"Rua das Flores, numero 200\"}]}"
```

**Resultado esperado:**
```json
{
	"message": "Ótimo! Para registrar o problema precisamos de mais alguns detalhes:\n\n1. **Localização** – Você já informou: Rua das Flores, nº 200.  \n2. **Descrição** – O que exatamente está acontecendo? (ex.: “há um buraco grande que pode causar acidentes”).  \n3. **Categoria** – Pelo que você descreveu, parece ser **Pavimentação** (buraco no asfalto/calçada).\n\nPor favor, me dê a descrição completa e confirmarei antes de redirecioná‑lo ao formulário já preenchido.",
	"intent": "report",
	"entities": {
		"location": "Rua das Flores",
		"description": "Rua das Flores, numero 200",
		"category": "Pavimentação"
	},
	"action": {
		"type": "navigate_to_form",
		"payload": {
			"location": "Rua das Flores",
			"description": "Rua das Flores, numero 200",
			"category": "Pavimentação"
		}
	}
}
```

---

## Documentação interativa da API

Com o container rodando, acesse: **http://localhost:8000/docs**

---

## Estrutura do projeto

```
modulo-de-ia/
├── chatbot/
│   ├── __init__.py     # Módulo Python
│   ├── agent.py        # Grafo LangGraph (orquestrador principal)
│   ├── tools.py        # Tool calls para o backend (somente leitura)
│   ├── prompts.py      # System prompt e mensagens padrão
│   └── api.py          # Endpoint POST /chat (FastAPI)
├── .env.example        # Modelo do arquivo de configuração
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GROQ_API_KEY` | ✅ Sim | Chave de API do Groq (obtenha em console.groq.com/keys) |
| `BACKEND_BASE_URL` | ❌ Não | URL do backend do Cidade Conectada (padrão: `http://localhost:3000`) |
| `PORT` | ❌ Não | Porta da API (padrão: `8000`) |

# Equipe
- Matheus Rangel Kirzner (Equipe 4 - 5° período)
