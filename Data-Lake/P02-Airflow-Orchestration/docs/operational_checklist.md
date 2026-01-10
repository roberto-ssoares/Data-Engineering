# ✅ Operational Checklist — Execução e Confiabilidade

Este documento descreve o **checklist operacional** para execução, validação e troubleshooting do Data Lake **Bronze → Silver → Gold**.

Ele reflete práticas utilizadas em **pipelines batch orquestrados por Airflow**, com foco em previsibilidade, observabilidade e segurança operacional.

---

## 1️⃣ Pré-requisitos de Ambiente

Antes de qualquer execução, valide:

### 🔹 Docker & Containers

- Docker Desktop em execução

- Containers do Airflow ativos

```bash
docker ps
```

- Volume `/opt/p01` montado corretamente

```bash
docker compose exec airflow-scheduler ls /opt/p01
```

### 🔹 Dependências Python

- pandas disponível no container do Airflow

```bash
docker compose exec airflow-scheduler python3 - << EOF
import pandas as pd
print(pd.__version__)
EOF
```

---

## 2️⃣ Checklist de Execução Manual (P02)

> **Sempre executar manualmente antes de rodar via DAG**

### 2.1 Raw → Bronze

```bash
docker compose exec airflow-scheduler \
  bash -lc "python3 /opt/airflow/scripts/run_raw_to_bronze.py"
```

Validar:

- Arquivos aparecem em `data/bronze`

- `_SUCCESS` criado

- `_SUCCESS` contém:
  
  - layer
  
  - utc_processed_at
  
  - run_id (ou `manual`)
  
  - logical_date

---

### 2.2 Bronze → Silver

```bash
docker compose exec airflow-scheduler \
  bash -lc "python3 /opt/airflow/scripts/run_bronze_to_silver.py"
```

Validar:

- Arquivos `.csv` criados em `data/silver`

- `_SUCCESS` criado

- Erro se **nenhum arquivo** for produzido

- Logs gravados em `logs/bronze_to_silver.log`

---

### 2.3 Silver → Gold (Basic)

```bash
docker compose exec airflow-scheduler \
  bash -lc "python3 /opt/airflow/scripts/run_silver_to_gold_basic.py"
```

Validar:

- Tabelas agregadas criadas

- `_SUCCESS` criado

- Métricas coerentes

---

### 2.4 Silver → Gold (Analytics)

```bash
docker compose exec airflow-scheduler \
  bash -lc "python3 /opt/airflow/scripts/run_silver_to_gold_analytics.py"
```

Validar:

- Tabelas analíticas criadas

- Execução resiliente (uma falha não quebra todas)

- `_SUCCESS` criado **somente se houver dados**

---

### 2.5 Silver → Gold (Advanced)

```bash
docker compose exec airflow-scheduler \
  bash -lc "python3 /opt/airflow/scripts/run_silver_to_gold_advanced.py"
```

Validar:

- `dim_localidade.csv` criado

- `fact_acidentes.csv` particionado:

```text
data/gold/
 └── ano=YYYY/
     └── mes=MM/
         └── fact_acidentes.csv
```

---

## 3️⃣ Execução via Airflow (FASE FINAL)

### 3.1 DAG Visível

```bash
docker compose exec airflow-webserver airflow dags list
```

Se falhar:

```bash
docker compose exec airflow-webserver airflow dags list-import-errors
```

---

### 3.2 Execução Manual da DAG

- Trigger manual no UI

- Tasks executam na ordem correta

- Logs visíveis por task

- Retry funciona corretamente

---

## 4️⃣ Validações Pós-Execução

### 🔹 Integridade das Camadas

- Bronze nunca altera arquivos raw

- Silver nunca altera bronze

- Gold não escreve fora de seu escopo

### 🔹 _SUCCESS

- Nunca existe `_SUCCESS` sem dados

- `_SUCCESS` é sempre o último artefato gerado

- Serve como evidência auditável

---

## 5️⃣ Flags Operacionais

### 🔁 Reprocessamento Completo

```bash
P02_FORCE_REPROCESS_SILVER=1
```

Valida:

- Camada limpa antes de executar

- Dados regenerados

- `_SUCCESS` reescrito

---

## 6️⃣ Logs & Observabilidade

Verificar:

```bash
logs/
├─ raw_to_bronze.log
├─ bronze_to_silver.log
├─ silver_to_gold_basic.log
├─ silver_to_gold_analytics.log
└─ silver_to_gold_advanced.log
```

- Logs consistentes

- Warnings não silenciosos

- Erros interrompem pipeline corretamente

---

## 7️⃣ Troubleshooting Rápido

### ❌ DAG não aparece

- Verificar erros de import

- Verificar `dags/`

- Verificar permissões

### ❌ pandas não encontrado

- Verificar ambiente do scheduler

- Verificar `_PIP_ADDITIONAL_REQUIREMENTS`

- Validar `sys.executable`

### ❌ `_SUCCESS` vazio

- Pipeline falhou silenciosamente

- Saída mínima não validada

- Corrigir script P02

---

## 8️⃣ Critérios de Qualidade Operacional

Este pipeline só é considerado **OK** se:

- Executa manualmente

- Executa via Airflow

- É idempotente

- Falha de forma explícita

- Deixa rastros (logs + markers)

---

## 9️⃣ Conclusão

Este checklist garante que o Data Lake:

- é previsível

- é auditável

- é reproduzível

- se comporta como pipeline de produção

Ele também demonstra **maturidade operacional**, não apenas conhecimento técnico.

---


