# 🔬 Technical Deep Dive — Data Lake Bronze / Silver / Gold

Este documento descreve **em profundidade técnica** as decisões arquiteturais, padrões de código, mecanismos de confiabilidade e trade-offs adotados no projeto **AWS Data Lake – Bronze / Silver / Gold**.

O foco aqui não é “o que faz”, mas **por que foi feito assim**.

---

## 1️⃣ Visão Geral da Arquitetura Técnica

A arquitetura segue o padrão clássico de **Data Lake em camadas**, com separação clara de responsabilidades:

| Camada | Responsabilidade      | Tipo de dado |
| ------ | --------------------- | ------------ |
| Raw    | Preservação           | Imutável     |
| Bronze | Ingestão confiável    | Estrutural   |
| Silver | Qualidade e semântica | Analítico    |
| Gold   | Negócio / consumo     | Otimizado    |

O pipeline foi projetado para ser:

- Determinístico

- Idempotente

- Auditável

- Reprocessável

---

## 2️⃣ Decisão-chave: Raw ≠ Bronze

### ❓ Por que manter Raw separado da Bronze?

Porque **Raw é contrato de origem**.

- Raw nunca é modificado

- Bronze pode ser reprocessado

- Silver pode ser reconstruído

- Gold pode ser descartado e recriado

Essa separação garante:

- Reprocessamento seguro

- Debug retroativo

- Compliance e auditoria

> Em produção, Raw equivale a **S3 Landing Zone** com versionamento.

---

## 3️⃣ Estratégia de Ingestão (Raw → Bronze)

### 🔹 Problema real tratado

- CSVs com encoding inconsistente

- Delimitadores variáveis

- Linhas malformadas

- Headers instáveis

### 🔹 Solução técnica

- Leitor robusto com fallback (`read_csv_flexible`)

- Preservação de schema original

- Zero regra de negócio

### 🔹 Decisão importante

Não há:

- Casting agressivo

- Drop de colunas

- Normalização

Isso evita **data loss silencioso**.

---

## 4️⃣ Bronze → Silver: Qualidade como contrato

### 🔹 Objetivo da Silver

Transformar dados “legíveis” em dados **confiáveis**.

### 🔹 Padrões adotados

#### Padronização

- Colunas em `snake_case`

- Remoção de ruído estrutural

#### Limpeza defensiva

- Apenas linhas totalmente vazias

- Nada de imputação automática

#### Conversão de tipos

- Datas: tentativa com log de falha

- Numéricos: `errors="coerce"`

> Falhar silenciosamente é proibido.  
> Logar e continuar é preferível.

---

## 5️⃣ Logging: Observabilidade de verdade

Todos os pipelines utilizam:

- Logging centralizado

- Níveis claros (`INFO`, `WARNING`, `ERROR`)

- Logs persistidos em disco

Isso permite:

- Debug pós-execução

- Análise de falhas

- Auditoria técnica

> Em Airflow, logs são parte do produto.

---

## 6️⃣ Gold em 3 níveis: decisão arquitetural

### ❓ Por que não um único Gold?

Porque **usuários de dados são diferentes**.

| Gold      | Público         | Uso        |
| --------- | --------------- | ---------- |
| Basic     | Analista júnior | Exploração |
| Analytics | BI              | Dashboards |
| Advanced  | Engenharia / DS | Produção   |

Essa separação:

- Evita sobrecarga desnecessária

- Facilita manutenção

- Permite SLAs diferentes

---

## 7️⃣ Gold Advanced: práticas de produção

### 🔹 Validação de Schema

Antes de qualquer enriquecimento:

- Verificação explícita de colunas obrigatórias

- Falha rápida se contrato for quebrado

Isso previne:

- Dashboards errados

- Métricas inconsistentes

- Decisões incorretas

---

### 🔹 Enriquecimento temporal

Criação explícita de:

- Ano

- Mês

- Dia

- Hora

- Período do dia

Essas colunas são:

- Determinísticas

- Reprocessáveis

- Independentes de BI

---

### 🔹 Modelagem Dimensional

Implementação de:

- `fact_acidentes`

- `dim_localidade`

Mesmo em CSV, o desenho segue:

- Grain claro

- Dimensões reutilizáveis

- Fato enxuta

> Formato muda. Conceito não.

---

### 🔹 Particionamento físico

Dados salvos em:

```
gold/
└── ano=YYYY/
    └── mes=MM/
        └── fact_acidentes.csv
```

Isso prepara o projeto para:

- Athena

- Spark

- Presto

- Trino

---

## 8️⃣ Orquestração com Airflow: lições reais

### 🔹 Erro clássico evitado

“Rodou com sucesso, mas não gerou dados.”

### 🔹 Solução adotada

- Snapshot antes/depois

- Validação de saída mínima

- `_SUCCESS` só se houver arquivos reais

Isso transforma o pipeline em:

- Idempotente

- Confiável

- Auditável

---

## 9️⃣ Estratégia de Reprocessamento

Cada camada possui:

- Flag `FORCE_REPROCESS`

- Limpeza controlada

- Reexecução segura

Isso evita:

- Gambiarras

- Deleções manuais

- Estados inconsistentes

---

## 🔟 Trade-offs conscientes

### ❌ O que **não** foi feito

- Spark (prematuro)

- Delta/Iceberg (overkill)

- Data Quality pesado (fora do escopo)

### ✅ O que foi priorizado

- Clareza arquitetural

- Robustez

- Evolução natural

---

## 1️⃣1️⃣ Como isso escala em produção?

Este projeto pode evoluir diretamente para:

- S3 como storage

- Glue Catalog

- Athena

- Spark Structured Streaming

- CI/CD

Sem refatoração estrutural.

---

## 🎯 Como usar este documento em entrevista

Você pode:

- Abrir com visão geral

- Aprofundar em decisões específicas

- Defender trade-offs

- Mostrar maturidade técnica

Este material é ideal para perguntas como:

- “Como você garante qualidade?”

- “Como lida com reprocessamento?”

- “Como evita sucesso falso?”

- “Como pensa arquitetura?”

---

## 🏁 Encerramento técnico

Este projeto não demonstra apenas **código funcional**.  
Demonstra **pensamento de Engenharia de Dados em nível profissional**.

Ferramentas mudam.  
Arquitetura bem pensada permanece.

---


