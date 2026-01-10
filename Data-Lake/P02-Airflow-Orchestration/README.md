# 🧩 **P02 – Orquestração de Data Lake com Apache Airflow (Docker)**

Este projeto demonstra **orquestração de pipelines batch** utilizando **Apache Airflow**, com execução via **Docker Compose**, aplicada a um **Data Lake no padrão Bronze → Silver → Gold**.

O foco do projeto é evidenciar **boas práticas de orquestração**, como dependências entre tarefas, retries, observabilidade e separação clara entre **lógica de dados** e **controle de execução**.

## 🎯 Objetivo do Projeto

- Orquestrar pipelines de dados do Data Lake (**Raw → Bronze → Silver → Gold**)

- Definir dependências explícitas entre etapas

- Demonstrar retries, controle de falhas e execução monitorada

- Manter **Airflow desacoplado da lógica de transformação**

> A lógica de dados permanece no **P01 – Data Lake Bronze/Silver/Gold**.  
> O Airflow atua exclusivamente como **orquestrador**.

## 🧱 Arquitetura de Orquestração

Fluxo lógico do DAG:

1. `raw_to_bronze`

2. `bronze_to_silver`

3. `silver_to_gold_basic`

4. `silver_to_gold_analytics`

5. `silver_to_gold_advanced`

Cada tarefa executa um **wrapper Python** localizado em `scripts/`, responsável por chamar os pipelines do P01.

## 📂 Estrutura do Projeto

```text
P02-Airflow-Orchestration/
├─ docker/
│  └─ docker-compose.yaml
├─ dags/
│  └─ datalake_bronze_silver_gold_dag.py
├─ scripts/
│  ├─ run_raw_to_bronze.py
│  ├─ run_bronze_to_silver.py
│  ├─ run_silver_to_gold_basic.py
│  ├─ run_silver_to_gold_analytics.py
│  └─ run_silver_to_gold_advanced.py
├─ .env.example
└─ README.md
```

## ▶️ Como Executar (Resumo)

1. Copiar o arquivo de ambiente:
   
   ```bash
   cp .env.example .env
   ```

2. Subir o Airflow:
   
   ```bash
   docker compose -f docker/docker-compose.yaml up -d
   ```

3. Acessar a interface do Airflow:
   
   ```
   http://localhost:8080
   ```

4. Ativar e executar o DAG `datalake_bronze_silver_gold_dag`

## 🔗 Integração com o Projeto P01

Este projeto orquestra os pipelines implementados em:

- **P01 – Data Lake (Bronze / Silver / Gold)**

Os wrappers em `scripts/` apenas delegam a execução, garantindo:

- reutilização de código

- separação de responsabilidades

- maior aderência a ambientes produtivos

## 🚀 Conceitos Demonstrados

- Orquestração de pipelines batch

- Apache Airflow com Docker

- Dependência entre tarefas (DAG)

- Execução resiliente com retries

- Monitoramento via Airflow UI

- Arquitetura desacoplada (orquestração × dados)
