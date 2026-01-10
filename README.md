# Data Engineering – Portfolio

Este repositório reúne meus **projetos práticos de Engenharia de Dados**, com foco em **pipelines, arquitetura de dados, orquestração e boas práticas orientadas à produção**.

A proposta é demonstrar a evolução natural de um ecossistema de dados: da construção de um Data Lake em camadas até a orquestração e observabilidade do pipeline.

## 🧱 Principais Conceitos Demonstrados



- Arquitetura de Data Lake (Bronze / Silver / Gold)
- Pipelines batch em Python (pandas), com extensão natural para PySpark
- Ingestão robusta (encoding, delimitadores, tolerância a falhas)
- Padronização, limpeza e enriquecimento de dados
- Camada Gold em múltiplos níveis de maturidade
- Modelagem analítica (fact + dimension)
- Particionamento (ano/mês)
- Logging estruturado
- Ambientes reprodutíveis (.venv)
- Orquestração com Apache Airflow (Docker)
- Código modular e orientado a pipelines



## 📂 Projetos

### 🔹 P01 – Data Lake (Bronze / Silver / Gold)

### 

**Objetivo:** Implementar um Data Lake completo seguindo o padrão **Bronze → Silver → Gold**, com pipelines progressivos e práticas orientadas à produção.

**Destaques:**

- Raw → Bronze: ingestão robusta de CSV (encoding/delimitadores/falhas)
- Bronze → Silver: padronização de schema, limpeza e conversão de tipos
- Silver → Gold em 3 níveis:
  - **Basic**: agregações simples e didáticas
  - **Analytics**: tabelas prontas para BI
  - **Advanced**: validação de schema, enriquecimento, modelagem dimensional e particionamento (ano/mês)
- Logging centralizado e estrutura modular



📁 Caminho:

Data-Lake/P01-Bronze-Silver-Gold/



### 🔹P02 – Orquestração com Apache Airflow (Docker)

**Objetivo:** Demonstrar orquestração de pipelines batch usando **Apache Airflow**, com execução via **Docker Compose**, encadeando etapas Raw → Bronze → Silver → Gold.

**Destaques:**

- DAG com dependências explícitas entre etapas
- Retries e controle de falhas
- Separação clara entre:
  - lógica de dados (P01)
  - orquestração e monitoramento (P02)
- Observabilidade via Airflow UI

📁 Caminho:
Data-Lake/P02-Airflow-Orchestration/



## 🚀 Tecnologias Utilizadas

- Python

- pandas

- Estrutura extensível para PySpark

- Conceitos aplicáveis a AWS (S3, Glue, Athena)

- Git / GitHub

- Docker / Docker Compose

- Apache Airflow

## 🎯 Objetivo do Repositório

Este repositório foi criado com foco em **portfólio profissional**, alinhado com desafios reais enfrentados por Engenheiros de Dados em ambientes corporativos.

Ele complementa meus projetos de **Ciência de Dados**, mantendo uma separação clara entre análise/modelagem e engenharia/pipelines.

## 📌 Próximos Projetos (Roadmap)

- P03 – Data Lake com PySpark (versão distribuída)
- P04 – Data Quality (Pandera / Great Expectations)
- P05 – Observabilidade e testes (unit/integration) para pipelines

---

## Contato

- LinkedIn: https://www.linkedin.com/in/roberto-dos-santos-soares/
