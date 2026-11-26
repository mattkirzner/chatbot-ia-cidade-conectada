# Chatbot de IA — SmartCitys

Módulo de IA para o app [SmartCitysComIA](https://github.com/mattkirzner/SmartCitysComIA): tira dúvidas, consulta ocorrências e sugere a categoria de um relato urbano. Este repositório é o serviço FastAPI (`POST /chat`). O aplicativo mobile, o Expo e o Keycloak ficam no outro Git.

Para a **AV2 da matéria de IA**, o professor não precisa do app. O caminho mínimo abaixo usa Docker, um JSON fictício e o log de uso dos dados.

---

## Compatível com o app

O contrato `POST /chat` é o mesmo que a aba **Assistente** do fork chama. O `userId` e o Bearer do Keycloak identificam o cidadão; o agente não grava ocorrência — o app abre o formulário para a pessoa confirmar.

| Uso | Repositório | Como |
|---|---|---|
| Só o módulo de IA (AV2) | este | `DATA_SOURCE=mock` e Docker, como nas seções seguintes |
| App com o assistente | [SmartCitysComIA](https://github.com/mattkirzner/SmartCitysComIA) | clone os dois lado a lado; no `.env` deste repo, `DATA_SOURCE=http` |

Com o app, o chatbot lê o gateway local (`http://host.docker.internal:8080` no Compose). Setup, emulador e problemas de Metro estão no README do app.

---

## Tecnologias utilizadas

| Tecnologia | Função |
|---|---|
| Python 3.11 | Linguagem do módulo |
| FastAPI e Uvicorn | API `POST /chat` e `GET /health` |
| LangGraph e LangChain Groq | Agente conversacional e tools |
| Groq (`openai/gpt-oss-20b`) | LLM, só se for conversar em linguagem natural |
| Pydantic | Contrato da API e rascunho de ocorrência |
| httpx | Leitura opcional do gateway SmartCitys |
| Docker Compose | Única forma documentada de subir o serviço |

---

## Como instalar e rodar (mínimo da AV2)

Instale o [Docker Desktop](https://www.docker.com/) com containers Linux e deixe-o aberto.

Na pasta deste repositório:

```powershell
copy .env.example .env
docker compose up --build
```

O arquivo `.env` é obrigatório para o Compose. A demonstração da AV2 **não usa Groq**: pode deixar `GROQ_API_KEY` como está no exemplo. Preencha a chave só se for conversar em `POST /chat`.

O serviço sobe em **http://localhost:8000**. Em outro terminal:

```powershell
curl.exe http://localhost:8000/health
```

Resposta esperada: `{"status":"ok","service":"chatbot-cidade-conectada"}`.

`DATA_SOURCE=mock` no `.env` faz o módulo ler `chatbot/data/ocorrencias.json`. Para o app, use `DATA_SOURCE=http` e recrie o container (`docker compose up --build`).

Para parar: `Ctrl+C` no terminal do Compose, ou `docker compose down`.

Os comandos de demonstração usam `docker compose exec chatbot ...` com o container no ar. O volume `./chatbot` grava o log em `chatbot/data/uso_dados.jsonl`.

---

## Mini dicionário de dados

Arquivo: `chatbot/data/ocorrencias.json` (12 registros fictícios). Não há nomes, e-mails nem telefones.

| Campo | Para o cidadão | Para a prefeitura |
|---|---|---|
| `id_denuncia` | Número do chamado para perguntar o status. | Identificador interno da ocorrência. |
| `cidadao_id` | Conta de teste dona da lista (`cidadao-ana`, `cidadao-bruno`, `cidadao-sem-historico`). | Liga o registro ao solicitante, sem dado pessoal real. |
| `titulo` | Título curto que aparece na lista. | Resumo para triagem. |
| `descricao` | O que está acontecendo na rua. | Detalhe usado na categorização e no atendimento. |
| `categoria` | Tipo do problema no vocabulário do app. | Fila da equipe responsável. |
| `regiao` | Região do estado em que o problema está. | Recorte territorial da demanda. |
| `endereco` | Ponto de referência informado. | Localização operacional da equipe. |
| `status` | Se o chamado está aberto, em análise ou resolvido. | Situação do fluxo de atendimento. |
| `prioridade` | Urgência percebida no relato. | Ordem de atendimento. |

Casos difíceis já no arquivo: `cidadao-ana` tem várias ocorrências; `cidadao-sem-historico` não tem nenhuma; `205` é a única `FISCALIZACAO`; o id `99999` **não existe**.

Alterar um `status` nesse JSON e repetir `docker compose exec chatbot python -m chatbot.demonstrar` muda a listagem impressa. O módulo só lê os dados por `chatbot/dados.py`.

---

## Funções de acesso

O agente e os scripts não abrem o JSON. Eles chamam:

| Função | Faz | Vazio ou erro |
|---|---|---|
| `listar_ocorrencias_do_cidadao(cidadao_id)` | Lista as ocorrências daquele cidadão de teste. | Lista vazia se não houver registros. |
| `buscar_ocorrencia(ocorrencia_id)` | Detalha um número de chamado. | `None` se o id não existir (ex.: `99999`). |
| `sugerir_categoria(descricao)` | Devolve um código de categoria do SmartCitys por palavras da descrição. | `OUTROS_EMPECILHOS` se nenhuma palavra casar. |

As ferramentas do LangGraph (`list_my_occurrences`, `get_occurrence`, `suggest_category`) só chamam essas funções no modo `mock`.

---

## Como gerar o log com três chamadas

Com o container no ar:

```powershell
docker compose exec chatbot python -m chatbot.demonstrar
```

Isso chama, nesta ordem:

1. `listar_ocorrencias_do_cidadao("cidadao-ana")` — vários registros;
2. `buscar_ocorrencia("99999")` — não encontrada;
3. `sugerir_categoria("Poste de luz apagado na esquina")` — `ILUMINACAO_PUBLICA`.

Cada chamada acrescenta uma linha em `chatbot/data/uso_dados.jsonl` (o arquivo não vai para o Git). Abra o `.jsonl` e confira três linhas com `quando`, `funcao`, `chamador` (`demonstrar`), `parametros` (só ids ou recorte da descrição), `registros` e `ok`.

---

## Como ver o resumo

```powershell
docker compose exec chatbot python -m chatbot.resumir_uso
```

O script conta chamadas por função, erros, identificadores mais vistos e ids da base que nunca foram buscados pelo número.

---

## Respostas (a), (b) e (c)

Ensaio com `docker compose exec chatbot python -m chatbot.demonstrar` seguido de `docker compose exec chatbot python -m chatbot.resumir_uso`:

- **(a)** O módulo mais usa a listagem de `cidadao-ana` (uma chamada que devolve 6 registros). Esse é o conjunto principal consultado.
- **(b)** Nenhum id da base foi buscado pelo número nas três chamadas. A ocorrência `205` (`FISCALIZACAO`, caso sem semelhantes) só aparece se alguém listar `cidadao-bruno` ou consultar esse id. Isso sugere um dado difícil de alcançar no roteiro mínimo da correção, não um erro do serviço.
- **(c)** Houve 1 erro esperado: `buscar_ocorrencia("99999")` registra `ok=false` porque o identificador não existe no JSON. A função devolve vazio; não é falha de instalação.

---

## Declaração de uso de IA generativa

Este módulo e a adaptação da AV2 foram escritos com apoio de assistente de código (Cursor) usando Grok 4.6 e Grok 4.7. Os dados são fictícios. A classificação em linguagem natural, quando usada, passa pela API do Groq; a demonstração da AV2 usa só regras e o JSON versionado. Não tratei dados pessoais. Revisei o que foi feito e sou completamente responsável pelo resultado.

---

## Conversar com o agente (opcional)

Com `GROQ_API_KEY` preenchida no `.env` e o Compose no ar:

```powershell
curl.exe -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"userId\": \"cidadao-ana\", \"conversationId\": \"conv_av2\", \"messages\": [{\"role\": \"user\", \"content\": \"Quais são os meus chamados?\"}]}"
```

O `userId` do corpo escolhe o cidadão de teste no JSON. Não é necessário Bearer no modo mock. Recrie o container depois de mudar o `.env` (`docker compose up --build`).
