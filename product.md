# Product — Módulo de Chatbot de IA
## Cidade Conectada

---

## 1. Contexto do Projeto Principal

O Cidade Conectada é um aplicativo mobile desenvolvido em React Native (iOS e Android) que conecta cidadãos ao poder público municipal. Sua função central é permitir que qualquer cidadão registre problemas de infraestrutura urbana — como buracos em vias, falhas na iluminação pública, problemas de saneamento, coleta de lixo irregular, entre outros — diretamente pelo smartphone, gerando chamados que são encaminhados às equipes responsáveis da prefeitura.

O app já possui um fluxo de reporte via formulário e um sistema de acompanhamento de chamados. O módulo de chatbot de IA é uma extensão desse ecossistema, adicionando uma camada conversacional de suporte ao usuário.

---

## 2. Problema de Negócio e Necessidade do Usuário

O app principal pode não ser intuitivo para todos os perfis de usuário. Cidadãos com menor familiaridade digital — incluindo idosos e pessoas com baixo letramento tecnológico — frequentemente encontram dificuldades para:

- Entender como navegar e utilizar as funcionalidades do app;
- Preencher corretamente o formulário de reporte (campo de localização, escolha de categoria, descrição adequada do problema);
- Acompanhar o status de chamados já abertos.

A ausência de orientação contextual dentro do app aumenta a taxa de abandono do fluxo de reporte e reduz a efetividade do serviço público.

---

## 3. Público-Alvo

O módulo de chatbot é destinado a **todos os usuários do app Cidade Conectada**, com ênfase especial em:

- Cidadãos com baixa familiaridade digital (idosos, pessoas com menor escolaridade);
- Usuários que utilizam o app pela primeira vez;
- Cidadãos que têm dúvidas sobre chamados já abertos.

As partes interessadas (stakeholders) do módulo incluem:
- A prefeitura municipal, que se beneficia da qualidade e completude dos chamados registrados;
- As equipes de infraestrutura, que recebem chamados melhor descritos e categorizados;
- Os cidadãos, que têm maior autonomia e clareza no uso do serviço.

---

## 4. Objetivo do Módulo

Desenvolver um módulo de chatbot de IA integrado ao app Cidade Conectada que:

1. Responda dúvidas gerais sobre o uso do app em linguagem natural e acessível;
2. Guie o cidadão no processo de abertura de chamados, coletando as informações necessárias por meio de conversa e pré-preenchendo o formulário ao final;
3. Permita a consulta de status e histórico de chamados do usuário autenticado;
4. Exiba mensagens de fallback amigáveis quando não for capaz de entender ou resolver a solicitação.

---

## 5. Benefícios Esperados

- **Redução de abandono:** O fluxo guiado diminui a desistência durante o preenchimento do reporte;
- **Melhoria na qualidade dos chamados:** Informações coletadas de forma estruturada resultam em chamados mais completos e bem descritos;
- **Inclusão digital:** Interface conversacional em linguagem simples torna o app acessível a um público mais amplo;
- **Autonomia do usuário:** O cidadão consegue tirar dúvidas e acompanhar seus chamados sem depender de suporte externo;
- **Eficiência operacional:** Chamados melhor categorizados facilitam o trabalho das equipes de infraestrutura da prefeitura.

---

## 6. Limites do Produto

O módulo de chatbot **não** irá:

- Criar, atualizar ou excluir chamados diretamente (toda escrita no backend é realizada pelo usuário via formulário);
- Escalar para atendimento humano;
- Suportar outros idiomas além do português brasileiro;
- Enviar notificações proativas ao usuário;
- Acessar dados de outros usuários que não o autenticado;
- Processar entrada por voz ou imagem na versão inicial;
- Realizar qualquer função relacionada a vendas, pagamentos ou serviços comerciais.
