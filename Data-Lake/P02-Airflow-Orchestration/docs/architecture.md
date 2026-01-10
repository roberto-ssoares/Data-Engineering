# 🏗️ Architecture — Data Lake Bronze / Silver / Gold

Este documento descreve a **arquitetura técnica e conceitual** do projeto **AWS Data Lake – Bronze / Silver / Gold**, incluindo fluxo de dados, responsabilidades de cada camada e estratégia de orquestração.

O objetivo é tornar explícito **como e por que** cada componente existe, refletindo práticas reais de Engenharia de Dados em ambientes produtivos.

---

## 1️⃣ Visão Conceitual (Cloud)

> **Cloud alvo (conceitual): AWS**

Embora o projeto seja executado localmente, ele foi desenhado para ser **cloud-ready**, seguindo padrões amplamente utilizados na AWS.

| Componente    | Equivalente AWS      |
| ------------- | -------------------- |
| `data/raw`    | S3 – Raw Zone        |
| `data/bronze` | S3 – Bronze          |
| `data/silver` | S3 – Silver          |
| `data/gold`   | S3 – Gold            |
| Airflow       | MWAA / EC2           |
| Python        | AWS Glue / EMR / ECS |

---

## 2️⃣ Visão Física (Execução Local)

- **Execução:** Local (Windows + Docker)

- **Orquestração:** Apache Airflow

- **Processamento:** Python (pandas)

- **Isolamento:** Docker + virtual environments

- **Persistência:** File system simulando Data Lake

```
Host (Windows)
 └── Docker
     └── Airflow Container
         ├── dags/
         ├── logs/
         └── scripts/        ← P02 (orquestração)

     └── Volume montado
         └── /opt/p01        ← P01 (transformação)
```

---

## 3️⃣ Diagrama Geral da Arquitetura

```text
                ┌────────────────────┐
                │   Fonte de Dados   │
                │  (CSV / Raw Files) │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │      RAW LAYER     │
                │   data/raw/        │
                │  Dados imutáveis   │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │    BRONZE LAYER    │
                │   data/bronze/     │
                │  Ingestão robusta  │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │    SILVER LAYER    │
                │   data/silver/     │
                │  Limpeza + Schema  │
                └─────────┬──────────┘
                          │
              ┌───────────┼─────────────────────────┐
              │           │                         │
              ▼           ▼                         ▼
   ┌────────────────┐ ┌────────────────┐ ┌────────────────────┐
   │ GOLD - BASIC   │ │ GOLD - ANALYT. │ │ GOLD - ADVANCED    │
   │ data/gold/     │ │ gold_analytics │ │ data/gold/         │
   │ Agregações     │ │ BI / Dashboards│ │ Fact + Dim + Part. │
   └────────────────┘ └────────────────┘ └────────────────────┘
```

---

## 4️⃣ Separação de Responsabilidades (P01 vs P02)

### 🔹 P01 — Camada de Transformação

Responsável exclusivamente por **lógica de dados**.

📁 `src/`

- ingestão

- limpeza

- enriquecimento

- agregações

- modelagem dimensional

**Características:**

- Executável localmente

- Independente de Airflow

- Código puro de transformação

---

### 🔹 P02 — Camada de Orquestração

Responsável por **controle operacional**.

📁 `airflow/scripts/`

- Execução dos pipelines P01

- Controle de reprocessamento

- Validação de saída mínima

- Escrita de `_SUCCESS`

- Integração com Airflow

**Características:**

- Nenhuma lógica de negócio

- Foco em confiabilidade e observabilidade

- Falha explícita em caso de inconsistência

---

## 5️⃣ Fluxo de Execução da DAG

```text
precheck_raw
      │
      ▼
raw_to_bronze
      │
      ▼
bronze_to_silver
      │
      ▼
┌─────────────── GOLD ───────────────┐
│                                    │
│ silver_to_gold_basic               │
│ silver_to_gold_analytics           │
│ silver_to_gold_advanced            │
│                                    │
└────────────────────────────────────┘
```

### Observações importantes:

- **Fan-out controlado** na camada Gold

- Falha em um Gold não impede os demais

- Cada task valida sua própria saída

---

## 6️⃣ Estratégia de Idempotência e Controle

Cada camada implementa:

- Snapshot antes/depois

- Detecção de mudanças

- Flags explícitas de reprocessamento

- Escrita controlada de `_SUCCESS`

### Exemplo de flag:

```bash
P02_FORCE_REPROCESS_SILVER=1
```

---

## 7️⃣ Estratégia de Observabilidade

- Logs por pipeline

- Logs capturados pelo Airflow

- Erros propagados corretamente

- Sem “sucesso silencioso”

📁 `logs/`

```
raw_to_bronze.log
bronze_to_silver.log
silver_to_gold_basic.log
silver_to_gold_analytics.log
silver_to_gold_advanced.log
```

---

## 8️⃣ Por que essa Arquitetura é Profissional?

Este projeto demonstra:

- Arquitetura em camadas realista

- Separação clara de responsabilidades

- Execução previsível e auditável

- Pronto para escalar (Spark, S3, Glue)

- Compatível com ambientes produtivos

---

## 9️⃣ Evoluções Naturais

- Substituir filesystem por S3

- Trocar pandas por PySpark

- Adicionar Data Quality

- Monitoramento com métricas

- CI/CD de DAGs

---

## 1️⃣0️⃣ Conclusão

A arquitetura implementada neste projeto não é acadêmica.

Ela reflete:

- decisões técnicas reais

- problemas reais

- soluções adotadas em ambientes de produção

Este Data Lake foi construído para **funcionar, escalar e ser mantido**.

---
