# ==============================================================================
# UNIOESTE - CPA: Dockerfile para Dashboard em Python / Streamlit
# Ideal para implantação pela equipe de TI (Docker / Kubernetes / Nuvem)
# ==============================================================================

FROM python:3.11-slim

# Evitar prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências de sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar os arquivos da aplicação
COPY . .

# Expor a porta padrão do Streamlit
EXPOSE 8501

# Healthcheck para monitoramento de contêiner pela equipe de TI
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando para iniciar o dashboard
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
