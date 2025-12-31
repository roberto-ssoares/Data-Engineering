# **AWS Data Lake – Bronze / Silver / Gold**

### Este repositório apresenta uma **arquitetura de Data Lake ponta a ponta**, implementada em Python, seguindo o modelo moderno de camadas **Bronze → Silver → Gold**.

O projeto demonstra como construir **pipelines de dados robustos, reprodutíveis e orientados à produção**, evoluindo desde a ingestão de dados brutos até datasets analíticos prontos para consumo por BI, Analytics e Machine Learning.



## **1. Objetivo do Projeto**

O objetivo deste projeto é demonstrar **boas práticas de Engenharia de Dados**, incluindo:

- Ingestão e preservação de dados brutos (**Bronze**)

- Padronização, limpeza e enriquecimento (**Silver**)

- Diferentes níveis de datasets orientados ao negócio (**Gold**)

- Ambientes reprodutíveis usando virtual environments dedicados

- Arquitetura limpa, código modular e logging estruturado

Este projeto foi concebido como um **case de portfólio em Engenharia de Dados**, alinhado com pipelines reais de mercado.



## **2. Visão Geral da Arquitetura**

**Cloud (conceitual):** AWS  
**Storage (lógico):** Amazon S3  
**Execução (local):** Python (pandas), com extensão natural para PySpark

### **Camadas de Dados**

- **raw/**  
  Arquivos originais, imutáveis, conforme recebidos

- **bronze/**  
  Dados padronizados, com ingestão robusta e mínima transformação

- **silver/**  
  Dados limpos, validados e enriquecidos

- **gold/**  
  Dados prontos para análise, BI e modelagem



## **3. Estrutura do Projeto**

```text
de-aws-datalake-bronze-silver-gold/
│
├─ .venv/                    # ambiente virtual isolado (não versionado)
├─ requirements.txt
├─ README.md
│
├─ data/
│   ├─ raw/                  # dados brutos
│   ├─ bronze/               # dados padronizados
│   ├─ silver/               # dados tratados e enriquecidos
│   └─ gold/                 # dados analíticos / de negócio
│
├─ logs/                     # logs de execução dos pipelines
│
├─ src/
│   ├─ ingestion/            # raw -> bronze
│   ├─ transformation/       # bronze -> silver -> gold
│   └─ utils/                # helpers compartilhados (IO, logging)
│
└─ notebooks/
    └─ 01_eda_and_schema_definition.ipynb
```



## **4. Ambiente Reprodutível (.venv)**

Cada projeto de Engenharia de Dados deve utilizar um **ambiente virtual isolado**.

Este projeto segue essa boa prática.

### **Por que isso é importante**

| Motivo                     | Explicação                                                  |
| -------------------------- | ----------------------------------------------------------- |
| Isolamento de dependências | Evita conflitos entre pandas, PySpark, Airflow, boto3, etc. |
| Reprodutibilidade          | Qualquer pessoa pode recriar o ambiente                     |
| Padrão profissional        | Prática comum em ambientes produtivos                       |
| Estabilidade               | Mantém o Python global limpo                                |

### **Setup do ambiente**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```


## **5. Visão Geral dos Pipelines**

### **5.1 Raw → Bronze**

- Ingestão robusta de arquivos CSV

- Tratamento automático de:
  
  - encoding
  
  - delimitadores
  
  - linhas malformadas

- Preservação máxima da estrutura original

**Script:**

```
src/ingestion/ingest_raw_to_bronze.py
```



### **5.2 Bronze → Silver**

- Padronização de nomes de colunas (`snake_case`)

- Remoção de linhas completamente vazias

- Conversão de tipos (datas e campos numéricos)

- Logging centralizado

- Pipeline defensivo e tolerante a falhas

**Script:**

```
src/transformation/bronze_to_silver.py
```



## **6. Pipelines Silver → Gold**

A camada Gold foi implementada propositalmente em **três níveis progressivos**, demonstrando maturidade crescente de Engenharia de Dados.



### **6.1 Gold – Basic**

**Objetivo:**  
Agregações simples e didáticas, ideais para análises iniciais.

**Características:**

- Uma agregação principal por script

- Lógica de negócio mínima

- Transformações claras e fáceis de entender

**Exemplos de saídas:**

- Total de acidentes por UF

- Taxa básica de mortalidade

**Script:**

```
src/transformation/silver_to_gold_basic.py
```



### **6.2 Gold – Analytics**

**Objetivo:**  
Gerar **tabelas analíticas prontas para dashboards**.

**Características:**

- Múltiplas visões analíticas no mesmo pipeline

- Execução resiliente (falha em uma visão não interrompe as demais)

- Ideal para ferramentas de BI (Power BI, Superset, Metabase)

**Exemplos de saídas:**

- Acidentes por UF

- Acidentes por tipo de acidente

- Acidentes por causa do acidente

- Acidentes por período do dia

**Script:**

```
src/transformation/silver_to_gold_analytics.py
```



### **6.3 Gold – Advanced (Orientado à Produção)**

**Objetivo:**  
Demonstrar **práticas de Engenharia de Dados em nível produtivo**.

**Características:**

- Validação de schema mínimo

- Enriquecimento do dataset (ano, mês, dia, período do dia)

- Modelagem dimensional (fact + dimension)

- Armazenamento particionado (`ano=YYYY/mes=MM`)

- Logging estruturado

- Tratamento elegante de erros

**Datasets gerados:**

- `dim_localidade.csv`

- `fact_acidentes.csv` (particionado por ano/mês)

**Script:**

```
src/transformation/silver_to_gold_advanced.py
```



## **7. Estratégia de Logging**

Todos os pipelines utilizam **logging centralizado**, implementado via helpers compartilhados.

- Logs gravados em `/logs`

- Formato consistente em todos os scripts

- Visibilidade clara de warnings, erros e fluxo de execução

Essa abordagem reflete pipelines batch orquestrados por ferramentas como Airflow.



## **8. Boas Práticas de Engenharia Demonstradas**

- Arquitetura de Data Lake em camadas

- Ambientes reprodutíveis

- Ingestão robusta

- Código modular e legível

- Evolução progressiva de complexidade

- Programação defensiva

- Modelagem orientada ao negócio



## **9. Próximos Passos**

Possíveis extensões futuras:

- Implementação com PySpark

- Orquestração com Apache Airflow

- Data Quality (Pandera / Great Expectations)

- Integração com serviços AWS (S3, Glue, Athena)


