# 📊 Data Quality — Estratégia e Controles

Este documento descreve a **estratégia de Data Quality (DQ)** aplicada ao Data Lake **Bronze → Silver → Gold**, explicitando **o que é validado, quando é validado e por quê**.

O objetivo não é apenas “limpar dados”, mas **garantir confiança, rastreabilidade e previsibilidade** nos datasets produzidos.

---

## 1️⃣ Princípios de Data Quality adotados

Este projeto segue os seguintes princípios:

| Princípio                      | Aplicação                             |
| ------------------------------ | ------------------------------------- |
| Separação de responsabilidades | Cada camada tem regras próprias       |
| Dados brutos imutáveis         | Bronze nunca altera o raw             |
| Validação progressiva          | Regras aumentam da Bronze para Gold   |
| Falha explícita                | Erros críticos interrompem o pipeline |
| Observabilidade                | Logs e `_SUCCESS` como evidência      |

---

## 2️⃣ Data Quality por Camada

### 🟤 Raw

**Objetivo:** Preservação total do dado original.

**Regras:**

- Nenhuma validação semântica

- Nenhuma transformação

- Apenas leitura

**Racional:**  
Raw é fonte de verdade. Se houver erro, ele deve ser tratado **a jusante**, nunca apagado.

---

### 🟠 Bronze — Qualidade Estrutural

**Objetivo:** Garantir que o dado é **tecnicamente processável**.

#### Regras aplicadas:

- Encoding detectado automaticamente

- Delimitador flexível

- Linhas malformadas ignoradas com log

- Arquivos não-CSV rejeitados

#### O que **não** é feito:

- Validação de domínio

- Remoção de nulos por regra de negócio

- Correções semânticas

**Exemplo de validação:**

```text
✔ Arquivo lido com sucesso
⚠ Linha malformada ignorada
❌ Arquivo não reconhecido
```

---

### ⚪ Silver — Qualidade Semântica

**Objetivo:** Garantir **consistência e interpretabilidade** dos dados.

#### Regras aplicadas:

- Padronização de colunas (`snake_case`)

- Remoção de linhas totalmente vazias

- Conversão defensiva de tipos:
  
  - datas
  
  - campos numéricos

- Preservação de nulos (quando relevantes)

#### Validações implícitas:

- Datas inválidas → log de warning

- Valores não numéricos → `NaN`

- Pipeline não quebra por erro isolado

**Racional:**  
Silver é a camada onde o dado passa a ter **significado**, mas ainda não carrega regras rígidas de negócio.

---

### 🟡 Gold — Qualidade Analítica e de Negócio

A camada Gold é dividida em **três níveis**, cada um com exigências crescentes.

---

## 3️⃣ Gold Basic — Qualidade Analítica Inicial

**Objetivo:**  
Agregações simples, com validações mínimas.

#### Regras:

- Colunas de agrupamento devem existir

- Métricas ausentes são ignoradas

- Falha apenas se colunas-chave não existirem

**Exemplo:**

```text
❌ Coluna 'uf' não encontrada → pipeline falha
```

---

## 4️⃣ Gold Analytics — Qualidade para BI

**Objetivo:**  
Produzir datasets confiáveis para dashboards.

#### Regras:

- Cada visão é isolada

- Falha em uma agregação não interrompe as demais

- Logs específicos por visão

**Benefício:**  
Dashboards não ficam indisponíveis por erro pontual.

---

## 5️⃣ Gold Advanced — Qualidade de Produção

**Objetivo:**  
Simular pipelines de produção corporativos.

### 5.1 Validação de Schema

Antes de qualquer processamento:

```python
REQUIRED_COLUMNS = {
  "data_inversa",
  "uf",
  "municipio",
  "tipo_acidente",
  "causa_acidente",
  "horario",
}
```

- ❌ Pipeline falha se alguma coluna obrigatória estiver ausente

- ✔ Log explícito com colunas faltantes

---

### 5.2 Enriquecimento Controlado

- Conversão de datas com fallback

- Criação de colunas derivadas:
  
  - ano
  
  - mês
  
  - dia
  
  - hora
  
  - período do dia

**Falhas tratadas com warning, não crash.**

---

### 5.3 Integridade das Tabelas

#### Fact Table

- Granularidade clara (1 linha = 1 acidente)

- Colunas numéricas opcionais

- Sem duplicação artificial

#### Dimension Table

- Remoção de duplicados

- Ordenação determinística

- Chaves naturais preservadas

---

## 6️⃣ Validação de Saída Mínima (_SUCCESS)

Uma regra crítica de Data Quality aplicada em **todas as camadas P02**:

> ❌ Nunca gerar `_SUCCESS` sem dados

Implementação:

- Contagem de arquivos após execução

- Se `data_files == 0` → erro

- `_SUCCESS` só é escrito no final

**Benefício:**  
Evita **falsos positivos operacionais**, muito comuns em pipelines imaturos.

---

## 7️⃣ Observabilidade & Evidência

### 🔍 Logs

- Logs por camada

- Mensagens claras

- Separação de warning vs erro

### 📌 `_SUCCESS`

Contém:

- camada

- timestamp UTC

- run_id

- logical_date

Serve como:

- evidência de execução

- checkpoint operacional

- insumo para auditoria

---

## 8️⃣ Evolução Natural de Data Quality

Este projeto foi desenhado para permitir evolução futura:

- Great Expectations

- Pandera

- Métricas de DQ (completeness, freshness, uniqueness)

- SLAs de dados

- Alertas via Airflow

---

## 9️⃣ Conclusão

A estratégia de Data Quality deste Data Lake:

- respeita o papel de cada camada

- evita overengineering precoce

- falha de forma explícita

- se aproxima de ambientes produtivos reais

Ela demonstra que **engenharia de dados não é apenas mover dados**, mas **garantir confiança no dado entregue**.

---


