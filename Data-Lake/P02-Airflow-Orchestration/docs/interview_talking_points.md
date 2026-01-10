# 🎯 Interview Talking Points — Data Lake Bronze / Silver / Gold

Este documento organiza os **principais pontos de fala** para explicar o projeto **AWS Data Lake – Bronze / Silver / Gold** em entrevistas técnicas e de negócio.

O foco é demonstrar **clareza conceitual, maturidade técnica e visão de produção**, evitando respostas acadêmicas ou superficiais.

---

## 1️⃣ Visão Geral (Pitch de 30 segundos)

> “Este projeto implementa uma arquitetura completa de Data Lake no padrão **Bronze → Silver → Gold**, cobrindo ingestão, tratamento, modelagem analítica e orquestração.  
> Ele foi construído com foco em **boas práticas de Engenharia de Dados**, reprodutibilidade e evolução gradual até padrões produtivos.”

---

## 2️⃣ Problema que o Projeto Resolve

**Contexto:**

- Dados brutos chegam com problemas de encoding, schema inconsistente e baixa qualidade

- Analistas precisam de datasets confiáveis e prontos para consumo

- Pipelines precisam ser auditáveis, reprocessáveis e resilientes

**Solução:**

- Separação clara de responsabilidades por camada

- Preservação do dado bruto

- Evolução progressiva da qualidade e do valor analítico

---

## 3️⃣ Por que Bronze / Silver / Gold?

**Bronze**

- Preservação máxima do dado

- Nenhuma regra de negócio

- Base para reprocessamento futuro

**Silver**

- Onde a qualidade nasce

- Padronização, limpeza, enriquecimento

- Dados confiáveis

**Gold**

- Dados orientados ao negócio

- Diferentes níveis de maturidade:
  
  - Basic (didático)
  
  - Analytics (BI)
  
  - Advanced (produção)

👉 *Essa separação reduz acoplamento e facilita evolução.*

---

## 4️⃣ Decisões Técnicas Importantes

### 4.1 Por que pandas e não Spark?

- Volume atual comporta processamento local

- Prioridade em clareza e didática

- Arquitetura preparada para migração futura para PySpark

> “Trocar pandas por Spark seria uma decisão de implementação, não de arquitetura.”

---

### 4.2 Por que múltiplos níveis de Gold?

- Demonstra maturidade progressiva

- Mostra que diferentes consumidores exigem diferentes datasets

- Evita um único pipeline monolítico

---

### 4.3 Por que validação de schema no Gold Advanced?

- Garante contratos de dados

- Evita propagação de erros

- Aproxima o pipeline de ambientes produtivos reais

---

## 5️⃣ Orquestração (P02 – Airflow)

**O que foi feito:**

- Wrappers que executam os pipelines do P01

- Controle de reprocessamento (`FORCE`)

- Escrita de `_SUCCESS` apenas quando há saída válida

- Execução sempre a partir de `/opt/p01` (evitando bugs de path)

**Por que isso importa:**

- Idempotência

- Observabilidade

- Auditabilidade

- Segurança operacional

---

## 6️⃣ Tratamento de Erros e Robustez

- Falha rápida quando diretórios não existem

- Logs claros e centralizados

- Execuções parciais no Gold Analytics

- Validação explícita de “saída mínima”

> “Prefiro falhar cedo e claramente do que gerar dados silenciosamente incorretos.”

---

## 7️⃣ Modelagem de Dados (Gold Advanced)

**Fato:**

- `fact_acidentes`

- Granularidade bem definida

- Particionamento por ano e mês

**Dimensão:**

- `dim_localidade`

- Preparada para evolução (SCD)

**Benefício:**

- Pronto para BI, SQL engines e ML

---

## 8️⃣ Qualidade de Dados

- Regras implícitas no Silver

- Validação explícita no Gold Advanced

- Estrutura preparada para frameworks de Data Quality

> “Qualidade não é uma etapa, é uma responsabilidade contínua.”

---

## 9️⃣ Observabilidade e Logging

- Logs por pipeline

- Mensagens semânticas

- Facilidade de troubleshooting

Isso aproxima o projeto de **ambientes com SLA e suporte 24/7**.

---

## 🔟 Evolução para Produção (se perguntarem)

Você pode responder:

- Migrar para S3

- Usar Glue Catalog

- Consultar com Athena

- Processar com Spark

- Orquestrar com Airflow gerenciado

- Adicionar Data Quality formal

- Implementar CI/CD

---

## 1️⃣1️⃣ Principais Aprendizados

- Importância de paths absolutos em ambientes orquestrados

- Diferença entre código “que roda” e código “operável”

- Valor da separação clara de responsabilidades

- Importância de validar saída mínima

---

## 1️⃣2️⃣ Pergunta Clássica: “O que você faria diferente?”

Resposta madura:

> “Nada estrutural. A arquitetura foi pensada para evoluir.  
> As melhorias seriam incrementais: escala, qualidade formal e cloud.”

---

## 🏁 Conclusão

Este projeto demonstra:

- Pensamento arquitetural

- Engenharia defensiva

- Clareza de propósito

- Maturidade para ambientes reais

---

### 
