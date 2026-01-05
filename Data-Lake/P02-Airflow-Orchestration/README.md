# 🧩 P02 – Orquestração de Pipelines com Apache Airflow

Este projeto demonstra **orquestração de pipelines batch** usando **Apache Airflow**, com execução via **Docker Compose**.

O objetivo aqui não é reimplementar a lógica de transformação de dados, e sim demonstrar como **orquestrar, agendar, monitorar e controlar falhas** em um pipeline de Data Lake.

## 🎯 Objetivo do Projeto (P02)

Demonstrar como **orquestrar pipelines batch** de um Data Lake usando **Apache Airflow**, cobrindo:

- Orquestrar o fluxo **Raw → Bronze → Silver → Gold**

- Definir dependências entre etapas

- Configurar retries e comportamento de falhas

- Manter separação clara entre:
  
  - **lógica de dados** (scripts do P01)
  - **orquestração** (DAGs do Airflow)



📌 Importante:  
O Airflow **não substitui** seus scripts Python — ele **orquestra** o que você já construiu no P01.


## 📁 Estrutura recomendada do P02

Crie um novo projeto **irmão** do P01:

```textile
Data-Engineering/ 
    └─ Data-Lake/ 
    ├─ P01-Bronze-Silver-Gold/ 
    └─ P02-Airflow-Orchestration/
```

### Estrutura interna do P02

```textile
P02-Airflow-Orchestration/ 
│ 
├─ docker-compose.yaml 
│ 
├─ dags/ 
|   │ 
|   └─ datalake_bronze_silver_gold_dag.py 
│ 
├─ plugins/ # (opcional) 
│ 
├─ logs/ # gerado pelo Airflow (não versionar) 
│ 
└─ scripts/ # wrappers para chamar P01 
│  ├─ run_raw_to_bronze.py
│  ├─ run_bronze_to_silver.py
│  ├─ run_silver_to_gold_basic.py
│  ├─ run_silver_to_gold_analytics.py
│  └─ run_silver_to_gold_advanced.py
├─ README.md 
└─ .env.example
```

📌 **Repare**:

- O P02 **não duplica lógica**

- Ele **chama os scripts do P01**

- Isso reflete ambiente real de produção



## 🧠 Conceito-chave (entrevista)

> “No meu portfólio, os pipelines de dados são independentes do Airflow.  
> O Airflow apenas orquestra, agenda e monitora.”

Essa frase é **fortíssima**.



## 🐳 Stack técnica do P02

Para portfólio, a melhor escolha é:

- **Apache Airflow**

- **Docker + docker-compose**

- Executor: `LocalExecutor` (simples e realista)

📌 Isso evita:

- dependência de instalação local

- problemas de ambiente

- ruído desnecessário



## 🔄 DAG principal (o que ele vai fazer)

Pipeline lógico:

```textile
raw_to_bronze 
    ↓ 
bronze_to_silver 
    ↓ 
silver_to_gold_basic 
    ↓ 
silver_to_gold_analytics 
    ↓ 
silver_to_gold_advanced`
```

Cada etapa:

- chama um script Python

- tem retries

- tem logging

- falha de forma controlada


## 📄 README.md do P02 (visão futura)

O README do P02 deve explicar:

1. O que é orquestração

2. Por que Airflow

3. Arquitetura do DAG

4. Como subir (`docker-compose up`)

5. Como visualizar no UI

Nada de código pesado no README — **arquitetura e intenção**.



## 🚀 Roadmap de implementação (ordem correta)

### Etapa 1 – Ambiente

- Criar `P02-Airflow-Orchestration/`

- Adicionar `docker-compose.yaml` padrão do Airflow

- Subir o Airflow localmente

### Etapa 2 – DAG simples

- Criar DAG com 3 tarefas dummy

- Validar execução no UI

### Etapa 3 – Integração com P01

- Criar scripts `run_*.py`

- Substituir tasks dummy por chamadas reais

### Etapa 4 – Robustez

- retries

- depends_on_past

- catchup=False

- logging claro






Perfeito. Vamos criar a **estrutura completa do P02** (pastas + README inicial + placeholders essenciais) de forma que você só precise copiar/criar os arquivos no lugar certo.

Abaixo está exatamente o que você deve criar em:

```
Data-Engineering/Data-Lake/P02-Airflow-Orchestration/
```

---

## 1) Estrutura de pastas (crie exatamente assim)

```text
P02-Airflow-Orchestration/
│
├─ README.md
├─ .gitignore
├─ .env.example
│
├─ dags/
│   └─ datalake_bronze_silver_gold_dag.py   # placeholder (vamos preencher na etapa C)
│
├─ scripts/
│   ├─ run_raw_to_bronze.py                 # placeholder (vamos preencher depois)
│   ├─ run_bronze_to_silver.py              # placeholder
│   ├─ run_silver_to_gold_basic.py          # placeholder
│   ├─ run_silver_to_gold_analytics.py      # placeholder
│   └─ run_silver_to_gold_advanced.py       # placeholder
│
└─ docker/
    └─ docker-compose.yaml                  # placeholder (vamos preencher na etapa B)
```

Observação: coloquei `docker-compose.yaml` dentro de `docker/` para separar “infra” do resto. Se você preferir, pode ficar na raiz do P02. Eu mantenho assim por organização.

---

## 2) Conteúdo do `.gitignore` (P02)

Crie `P02-Airflow-Orchestration/.gitignore`:

```gitignore
# Airflow
logs/
plugins/
airflow.db
webserver_config.py
__pycache__/

# Env
.env

# OS
.DS_Store
Thumbs.db
```

---

## 3) Conteúdo do `.env.example`

Crie `P02-Airflow-Orchestration/.env.example`:

```env
# Airflow admin user (example)
AIRFLOW_UID=50000
AIRFLOW_GID=0

# Optional: set a custom admin credentials later (if needed)
# _AIRFLOW_WWW_USER_USERNAME=admin
# _AIRFLOW_WWW_USER_PASSWORD=admin
```

Depois, você pode copiar para `.env` (que será ignorado pelo Git).

---

## 4) README.md inicial (P02) — pronto para portfólio

Crie `P02-Airflow-Orchestration/README.md`:

```markdown
# P02 – Orquestração com Apache Airflow (Docker)

Este projeto demonstra **orquestração de pipelines batch** usando **Apache Airflow**, com execução via **Docker Compose**.

O objetivo aqui não é reimplementar a lógica de transformação de dados, e sim demonstrar como **orquestrar, agendar, monitorar e controlar falhas** em um pipeline de Data Lake.

---

## Objetivo

- Orquestrar o fluxo **Raw → Bronze → Silver → Gold**
- Definir dependências entre etapas
- Configurar retries e comportamento de falhas
- Manter separação clara entre:
  - **lógica de dados** (scripts do P01)
  - **orquestração** (DAGs do Airflow)

---

## Arquitetura de Orquestração

Fluxo lógico:

1. `raw_to_bronze`
2. `bronze_to_silver`
3. `silver_to_gold_basic`
4. `silver_to_gold_analytics`
5. `silver_to_gold_advanced`

Cada etapa chama um script Python (wrappers em `scripts/`) que executa a lógica do pipeline.

---

## Estrutura do Projeto

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

---

## Como rodar (preview)

> Observação: o `docker-compose.yaml` e o DAG serão implementados nas próximas etapas do projeto.

Passos previstos:

1. Copiar `.env.example` para `.env`

2. Subir o Airflow:
   
   ```bash
   docker compose -f docker/docker-compose.yaml up -d
   ```

3. Acessar Airflow UI (local)

4. Executar o DAG e acompanhar logs

---

## Integração com o P01

O P02 será integrado ao projeto:

- **P01 – Data Lake (Bronze/Silver/Gold)**

O Airflow executará wrappers em `scripts/` que chamam os pipelines do P01.

---

## Próximas Entregas

- `docker-compose.yaml` funcional para Airflow

- DAG inicial com tarefas encadeadas

- Execução real dos scripts do P01 via wrappers

- Logs claros + retries configurados

- Documentação final e prints do Airflow UI

```
---

## 5) Placeholders mínimos dos arquivos (para evitar pastas vazias)

### 5.1 DAG placeholder

Crie `dags/datalake_bronze_silver_gold_dag.py`:

```python
"""
DAG placeholder.

Na próxima etapa, este arquivo terá a DAG completa do Data Lake:
Raw -> Bronze -> Silver -> Gold (Basic/Analytics/Advanced)
"""
```

### 5.2 Scripts placeholders

Crie cada arquivo em `scripts/` com esse conteúdo base (um por arquivo):

Ex.: `scripts/run_raw_to_bronze.py`

```python
"""
Wrapper placeholder.

Na próxima etapa, este script vai chamar a execução do pipeline do P01
correspondente a Raw -> Bronze.
"""
```

Repita o mesmo padrão para os outros wrappers.

### 5.3 docker-compose placeholder

Crie `docker/docker-compose.yaml`:

```yaml
# docker-compose placeholder
# Na próxima etapa, este arquivo terá a stack do Apache Airflow via Docker Compose.
services: {}
```

---

## 6) O que você faz agora (execução rápida)

1. Crie a pasta `P02-Airflow-Orchestration/` dentro de `Data-Engineering/Data-Lake/`

2. Crie as subpastas: `docker/`, `dags/`, `scripts/`

3. Crie os arquivos com os conteúdos acima

4. Faça commit e push

Comandos:

```bash
git add .
git commit -m "Add P02 Airflow orchestration project structure"
git push
```

---
