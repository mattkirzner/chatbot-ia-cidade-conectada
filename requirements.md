# Requirements — Módulo de Chatbot de IA
## Cidade Conectada

---

## Histórias de Usuário e Critérios de Aceitação

---

### US-01 — Dúvidas Gerais sobre o App

**Como** cidadão usuário do app Cidade Conectada,
**quero** fazer perguntas em linguagem natural sobre como usar o app,
**para** entender as funcionalidades sem precisar de ajuda externa.

**Critérios de Aceitação (EARS):**

O MÓDULO DE CHATBOT DEVERÁ responder a perguntas sobre funcionalidades do app em português brasileiro em todas as interações.

QUANDO o usuário enviar uma pergunta sobre como usar o app, O MÓDULO DE CHATBOT DEVERÁ retornar uma resposta em linguagem clara e objetiva, sem jargões técnicos.

QUANDO o usuário enviar uma mensagem em branco ou com apenas espaços, O MÓDULO DE CHATBOT DEVERÁ exibir uma mensagem solicitando que o usuário escreva sua dúvida.

---

### US-02 — Guia de Abertura de Chamado

**Como** cidadão que identificou um problema de infraestrutura urbana,
**quero** ser guiado pelo chatbot para descrever o problema em linguagem natural,
**para** não precisar preencher manualmente todos os campos do formulário.

**Critérios de Aceitação (EARS):**

QUANDO o usuário indicar que deseja reportar um problema, O MÓDULO DE CHATBOT DEVERÁ iniciar um fluxo de coleta de dados solicitando, sequencialmente, a localização, a descrição do problema e confirmando a categoria sugerida.

ENQUANTO o fluxo de coleta de dados estiver em andamento, O MÓDULO DE CHATBOT DEVERÁ manter o contexto da conversa e não perder informações já fornecidas pelo usuário.

QUANDO o usuário fornecer uma descrição do problema, O MÓDULO DE CHATBOT DEVERÁ extrair e estruturar ao menos os campos: localização (texto ou referência), descrição e categoria sugerida.

SE o usuário não fornecer a localização durante o fluxo de coleta, ENTÃO O MÓDULO DE CHATBOT DEVERÁ solicitar a informação novamente antes de prosseguir para o formulário.

---

### US-03 — Pré-preenchimento do Formulário de Reporte

**Como** cidadão que concluiu a conversa de reporte com o chatbot,
**quero** ser redirecionado ao formulário de chamado já com os campos preenchidos,
**para** revisar e enviar o reporte sem precisar digitar as informações novamente.

**Critérios de Aceitação (EARS):**

QUANDO o chatbot concluir a coleta dos dados de reporte, O MÓDULO DE CHATBOT DEVERÁ navegar para a tela de formulário com os campos localização, descrição e categoria preenchidos com os dados extraídos da conversa.

QUANDO os dados coletados estiverem incompletos, O MÓDULO DE CHATBOT DEVERÁ navegar para o formulário com os campos disponíveis preenchidos e os campos faltantes em branco para preenchimento manual pelo usuário.

---

### US-04 — Consulta de Status de Chamados

**Como** cidadão com chamados abertos no app,
**quero** perguntar ao chatbot sobre o status dos meus chamados,
**para** acompanhar o andamento sem precisar navegar manualmente pelo app.

**Critérios de Aceitação (EARS):**

QUANDO o usuário autenticado solicitar o status de um chamado específico pelo número, O MÓDULO DE CHATBOT DEVERÁ retornar o status atual daquele chamado conforme os dados disponíveis no backend.

QUANDO o usuário autenticado solicitar a listagem de seus chamados, O MÓDULO DE CHATBOT DEVERÁ retornar a lista de chamados do usuário com identificador, descrição resumida e status de cada um.

O MÓDULO DE CHATBOT DEVERÁ acessar apenas os chamados do usuário autenticado, nunca retornando dados de outros usuários.

SE o chamado consultado não existir ou não pertencer ao usuário autenticado, ENTÃO O MÓDULO DE CHATBOT DEVERÁ informar que o chamado não foi encontrado, sem expor detalhes técnicos do erro.

---

### US-05 — Fallback e Mensagens de Erro Amigáveis

**Como** cidadão que enviou uma mensagem que o chatbot não conseguiu processar,
**quero** receber uma resposta clara e orientativa,
**para** entender o que posso fazer a seguir sem me sentir bloqueado.

**Critérios de Aceitação (EARS):**

QUANDO o chatbot não identificar uma intenção reconhecível na mensagem do usuário, O MÓDULO DE CHATBOT DEVERÁ exibir uma mensagem amigável em português brasileiro explicando que não entendeu e sugerindo alternativas de ação (como reportar um problema, consultar chamados ou reformular a pergunta).

O MÓDULO DE CHATBOT DEVERÁ apresentar ao menos duas sugestões de ação ao exibir uma mensagem de fallback.

SE o serviço de LLM estiver indisponível, ENTÃO O MÓDULO DE CHATBOT DEVERÁ exibir uma mensagem informando que o serviço está temporariamente indisponível e orientar o usuário a utilizar o app diretamente.

---

### US-06 — Sugestão Automática de Categoria

**Como** cidadão que está descrevendo um problema de infraestrutura,
**quero** que o chatbot sugira automaticamente a categoria mais adequada para o meu relato,
**para** não precisar conhecer previamente as categorias disponíveis no sistema.

**Critérios de Aceitação (EARS):**

QUANDO o usuário fornecer uma descrição de um problema de infraestrutura, O MÓDULO DE CHATBOT DEVERÁ sugerir uma categoria com base no conteúdo da descrição e apresentá-la ao usuário para confirmação ou correção.

QUANDO o usuário discordar da categoria sugerida, O MÓDULO DE CHATBOT DEVERÁ permitir que o usuário descreva a categoria de forma livre, registrando essa descrição para o formulário.

---

## Restrições e Requisitos Não Funcionais

**RNF-01 — Idioma:**
O MÓDULO DE CHATBOT DEVERÁ operar exclusivamente em português brasileiro em todas as respostas geradas.

**RNF-02 — Plataforma:**
O MÓDULO DE CHATBOT DEVERÁ ser compatível com o app mobile Cidade Conectada desenvolvido em React Native, funcionando em dispositivos iOS e Android.

**RNF-03 — Acesso ao Backend:**
O MÓDULO DE CHATBOT DEVERÁ realizar apenas operações de leitura no backend do Cidade Conectada, sem criar, atualizar ou excluir registros diretamente.

**RNF-04 — Acessibilidade:**
O MÓDULO DE CHATBOT DEVERÁ utilizar linguagem simples, direta e sem jargões técnicos em todas as respostas, de forma a ser compreensível para usuários com diferentes níveis de letramento digital.
