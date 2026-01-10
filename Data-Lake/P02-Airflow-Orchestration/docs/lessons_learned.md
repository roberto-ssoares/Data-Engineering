# 📘 Lessons Learned — AWS Data Lake (Bronze / Silver / Gold)

Este documento registra os **principais problemas enfrentados**, **decisões técnicas tomadas** e **aprendizados consolidados** durante o desenvolvimento do projeto **AWS Data Lake – Bronze / Silver / Gold**.

O objetivo é demonstrar **maturidade em Engenharia de Dados**, evidenciando como desafios reais foram diagnosticados, corrigidos e incorporados à arquitetura final.

---

## 1️⃣ Separação entre Transformação (P01) e Orquestração (P02)

### 🔴 Problema encontrado

Inicialmente, scripts de transformação (P01) eram executados diretamente, sem uma camada clara de orquestração. Isso gerava:

- Forte acoplamento entre execução e lógica de negócio

- Dificuldade para reprocessamentos controlados

- Pouca visibilidade de falhas por etapa

### ✅ Decisão técnica

Foi introduzida uma **camada de orquestração (P02)** baseada em Apache Airflow, com:

- Scripts *wrappers* (`run_*.py`) responsáveis apenas por:
  
  - executar pipelines do P01
  
  - controlar reprocessamento
  
  - validar saída mínima
  
  - gerar marcadores `_SUCCESS`

### 📚 Aprendizado

> **Transformação de dados e orquestração devem ser responsabilidades distintas.**

Essa separação:

- facilita testes locais

- melhora observabilidade

- aproxima o projeto de ambientes produtivos reais

---

## 2️⃣ Caminhos Relativos vs Caminhos Absolutos em Ambientes Orquestrados

### 🔴 Problema encontrado

Scripts funcionavam localmente, mas falhavam quando executados via Airflow/Docker devido a:

- uso de caminhos relativos (`data/bronze`, `logs/`)

- diretório de execução (`cwd`) diferente do esperado

### ✅ Decisão técnica

Padronização total de paths com base no **root do projeto** (`/opt/p01`):

- Uso de `Path(__file__).resolve()` para derivar diretórios

- Execução sempre com `cwd=/opt/p01`

- Ajuste explícito de `PYTHONPATH`

### 📚 Aprendizado

> **Código que funciona localmente não é necessariamente código pronto para orquestração.**

Ambientes orquestrados exigem:

- paths determinísticos

- controle explícito de contexto de execução

---

## 3️⃣ Dependências Python no Airflow (pandas “sumindo”)

### 🔴 Problema encontrado

Tasks falhavam com:

```text
ModuleNotFoundError: No module named 'pandas'
```

Mesmo com `pandas` instalado no container.

### 🔍 Diagnóstico

O problema não estava no Airflow em si, mas em:

- execução via `subprocess`

- contexto de ambiente Python diferente

- `PYTHONPATH` sobrescrito incorretamente

### ✅ Decisão técnica

Correções aplicadas:

- Garantir uso do mesmo Python do Airflow

- Fazer **append** no `PYTHONPATH` (não overwrite)

- Validar `sys.executable` e versões dentro do container

### 📚 Aprendizado

> **Ambientes Docker + Airflow exigem verificação explícita do runtime Python.**

Nunca assumir:

- path do interpretador

- ambiente ativo

- herança automática de dependências

---

## 4️⃣ Marcador `_SUCCESS` sem dados (falso positivo)

### 🔴 Problema encontrado

Pipelines geravam `_SUCCESS` mesmo quando:

- nenhum arquivo de saída era produzido

- etapa falhava silenciosamente

- diretório de destino permanecia vazio

Isso gerava **falsos positivos** na orquestração.

### ✅ Decisão técnica

Implementada **validação de saída mínima**:

- Se `data_files == 0` → pipeline falha

- `_SUCCESS` só é escrito após validação

- Falha explícita interrompe DAG

### 📚 Aprendizado

> **Um pipeline que “termina” não é necessariamente um pipeline que “funcionou”.**

Validação de output é essencial para:

- confiabilidade

- downstream correto

- auditoria

---

## 5️⃣ Idempotência e Reprocessamento Controlado

### 🔴 Problema encontrado

Reexecuções podiam:

- sobrescrever dados silenciosamente

- gerar resultados inconsistentes

- dificultar debugging

### ✅ Decisão técnica

Introdução de flags de controle:

```bash
P02_FORCE_REPROCESS_BRONZE=1
P02_FORCE_REPROCESS_SILVER=1
P02_FORCE_REPROCESS_GOLD_ANALYTICS=1
```

Comportamento:

- limpeza explícita de camada

- logs claros de reprocessamento

- comportamento previsível

### 📚 Aprendizado

> **Reprocessar dados deve ser uma decisão explícita, não um efeito colateral.**

---

## 6️⃣ Gold em Níveis (Basic, Analytics, Advanced)

### 🔴 Observação de design

Nem todo consumidor de dados precisa do mesmo nível de complexidade.

### ✅ Decisão técnica

Implementação de **três níveis de Gold**:

| Nível     | Objetivo                        |
| --------- | ------------------------------- |
| Basic     | Didático, agregações simples    |
| Analytics | Dashboards e BI                 |
| Advanced  | Produção, modelagem dimensional |

### 📚 Aprendizado

> **Uma boa arquitetura de dados oferece múltiplas “portas de entrada” para o negócio.**

---

## 7️⃣ Logging como Cidadão de Primeira Classe

### 🔴 Problema inicial

Logs dispersos, inconsistentes ou inexistentes.

### ✅ Decisão técnica

Logging padronizado em todos os pipelines:

- helpers compartilhados

- arquivos por pipeline

- mensagens claras de erro e warning

### 📚 Aprendizado

> **Sem logs, não existe pipeline produtivo — apenas scripts.**

---

## 8️⃣ Conclusão

Este projeto reforçou princípios fundamentais de Engenharia de Dados:

- Separação de responsabilidades

- Execução determinística

- Validação explícita

- Observabilidade

- Tolerância a falhas

Os desafios enfrentados e resolvidos refletem **problemas reais de pipelines batch em produção**, tornando este projeto um **case sólido de portfólio profissional**.

---

## 
