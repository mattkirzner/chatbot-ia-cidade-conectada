FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Instala dependências primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY chatbot/ ./chatbot/

# Expõe a porta da API
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "chatbot.api:app", "--host", "0.0.0.0", "--port", "8000"]
