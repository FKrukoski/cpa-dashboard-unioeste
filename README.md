# 🎓 UNIOESTE | CPA - Dashboard Interativo de Autoavaliação Institucional (Python / Streamlit)

Este diretório contém a versão completa em **Python (Streamlit + Plotly)** do Painel Interativo de Autoavaliação Institucional da **Comissão Própria de Avaliação (CPA)** da Universidade Estadual do Oeste do Paraná (**UNIOESTE**).

---

## 🎯 Por que a versão em Python?

1. **Facilidade de Implantação para a TI da UNIOESTE:** A equipe de TI tem preferência e familiaridade natural com contêineres Docker, servidores Linux e ecossistemas Python (`pip`, `uv`, `poetry`, `FastAPI`, `Streamlit`).
2. **Performance Instantânea (< 0.5s):** As bases de dados foram convertidas para o padrão colunar de alta compressão **Apache Parquet**, permitindo filtros em milissegundos para os mais de 300.000 registros de respostas.
3. **Paridade Visual e Metodológica Integral:** Contém exatamente os mesmos 5 níveis Likert oficiais do SINAES, os mesmos filtros em cascata, cards de KPI dinâmicos, matrizes de calor, gráficos com controle de zoom no texto e matriz de plano de ação.

---

## 📁 Estrutura de Arquivos

```
Dash em Python/
├── app.py                     # Aplicação principal Streamlit
├── utils_dashboard.py         # Módulo de métricas Likert e construtores de gráficos Plotly
├── gerador_relatorio_pdf.py   # Gerador de relatório PDF do Plano de Ação em A4 paisagem
├── requirements.txt           # Dependências mínimas de pacotes Python
├── Dockerfile                 # Configuração oficial para contêiner Docker (para TI)
├── .gitignore                 # Arquivo de exclusão do Git (ignora CSV pesado de 122MB)
├── README.md                  # Este manual de execução e implantação
├── .streamlit/
│   └── config.toml            # Tema institucional (cores UNIOESTE #1B365D / #2166AC)
└── data/
    ├── base_respostas_longa_cpa.parquet  # Base colunar ultra-rápida (305.656 respostas, 191 KB)
    ├── paineis_executivos_campi.csv      # Pré-cálculos de forças e melhorias por campus
    ├── dissonancias_executivas_campi.csv # Maiores divergências de opinião intergrupos
    ├── participacao_campi.csv            # Contagem e percentuais de respondentes por segmento
    ├── dicionario_perguntas_completo.csv # Mapeamento SINAES de questões e segmentos
    ├── dicionario_vinculacao_topicos.csv # Tópicos unificados entre questionários
    ├── mapa_eixos.json                   # Mapeamento oficial dos 6 Eixos SINAES/CPA
    └── mapa_dimensoes.json               # Mapeamento oficial das Dimensões SINAES
```

---

## 🚀 Como Rodar Localmente

### 1. Pré-requisitos
Certifique-se de ter o Python 3.9+ instalado.

### 2. Instalar as dependências
Abra o terminal na pasta `Dash em Python` e execute:
```bash
pip install -r requirements.txt
```

### 3. Iniciar o Dashboard
Execute o comando:
```bash
streamlit run app.py
```
O navegador abrirá automaticamente no endereço: `http://localhost:8501`.

---

## 🌐 Opções de Hospedagem e Compartilhamento

### Opção A: Streamlit Community Cloud (Gratuito no GitHub - Demonstração Imediata)
Ideal para você compartilhar com os colegas da CPA antes da publicação oficial pela universidade:
1. Suba esta pasta `Dash em Python` para um repositório no seu GitHub pessoal (público ou privado).
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte sua conta do GitHub.
3. Aponte para o repositório e selecione o arquivo `app.py`.
4. Em menos de 2 minutos você terá um link seguro (`https://unioeste-cpa.streamlit.app`) acessível de qualquer computador ou celular.

### Opção B: Implantação pela TI da UNIOESTE (Via Docker)
A equipe de TI pode subir o painel em qualquer servidor institucional em apenas 2 comandos:
```bash
# Construir a imagem Docker
docker build -t unioeste-cpa-dashboard .

# Rodar o contêiner na porta desejada (ex: 80 ou 8501)
docker run -d -p 8501:8501 --name cpa_app unioeste-cpa-dashboard
```
Depois basta apontar um subdomínio reverso (ex: `https://cpa.unioeste.br/dashboard`) com Nginx ou Traefik.

---

## 📊 Funcionalidades Contempladas

1. **🎯 Painel Executivo:**
   - 4 Cards de KPI dinâmicos: *Total de Respondentes*, *Taxa de Favorabilidade (P4+P5)*, *Índice de Neutralidade (P3)* e *Taxa de Desfavorabilidade (P1+P2)*.
   - **Top 10 Forças Institucionais:** Barras empilhadas 100% Likert com tabela quantitativa completa abaixo.
   - **Top 10 Oportunidades de Melhoria:** Itens críticos com tabela completa abaixo.
   - **Principais Dissonâncias:** Questões com maior discrepância de percepção entre segmentos ($\Delta$ Dissonância).
   - **Participação por Segmento:** Gráfico donut interativo e tabela com total e percentuais.
2. **📊 Eixos & Dimensões:**
   - **Filtros Progressivos & Agrupamento:** Seleção guiada (Campus $\rightarrow$ Eixo $\rightarrow$ Dimensões) com opção de agrupar todas as dimensões do eixo.
   - **Matriz de Calor (Heatmap):** Taxa de favorabilidade cruzando Tópicos vs Segmentos.
   - **Distribuição Likert Completa:** 100% empilhada com rótulos alinhados à esquerda, sem vazios e fonte nítida.
   - **Tabela Quantitativa da Dimensão:** N, frequências P1 a P5, mediana e IIQ.
3. **🏛️ Benchmark Cross-Campi:**
   - Comparativo campus a campus para qualquer pergunta com alternância entre barras empilhadas e agrupadas.
   - Busca em texto livre de perguntas sem truncamento de enunciado.
4. **🌐 Visão Consolidada Macro:**
   - Visualização das Top N questões (com limite dinâmico por eixo) ordenadas por Favorabilidade, Desfavorabilidade ou sequência SINAES.
5. **📋 Plano de Ação Estratégico:**
   - Matriz automática com sugestão do setor responsável (PRORH, PRPPG, PROGRAD, Reitoria, etc.) e botões para **Exportar em PDF formatado (A4 Paisagem)**, **Excel (.xlsx)** e **CSV**.
