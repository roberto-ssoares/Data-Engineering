# DDL aderente ao header real



O índice geral também está correto (20 arquivos inspecionados no total).

Abaixo eu te devolvo:

1. **Checklist do que usar (2023)**

2. **DDL final (Bronze/Silver/Gold + Meta) já alinhado às colunas reais de 2023**

3. **2 decisões de governança importantes** (para suportar novos anos sem dor)

---

## 1) Quais arquivos de 2023 são “os certos”

Para o DDL e o mapeamento, os principais são os `__columns.json`:

- Conceito Enade 2023 (aba `PLANILHA_ENADE`)

- CPC 2023 (aba `CPC_2023`)

- IDD 2023 (aba `IDD_2023`)

- IGC 2023 (abas `IGC`, `matrículas_2021_2022_2023`, `Programas CAPES`)

Os `__schema.json` são ótimos para conferir preview/abas (ex.: IGC tem 3 abas e isso muda entre anos).

---

## 2) DDL final aderente às colunas reais (2023)

### Padrão que vou aplicar

- **Bronze**: guarda “como veio do INEP” + metadados (`ano_enade`, `ingest_date`, `source_file`)

- **Silver**: padroniza nomes/strings e cria chaves (`co_ies`, `co_curso`, `co_area`, etc.)

- **Gold**: views analíticas.

> Observação: alguns arquivos têm “*” e “**” no header (ex.: `Nome da IES*`). Eu vou normalizar no DDL removendo `*` e padronizando `snake_case`, mas mantendo a semântica. Isso facilita tudo (SQL, joins e código).

---

### 2.1 Schemas + Meta (governança e incremental)

```sql
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS meta;

CREATE TABLE IF NOT EXISTS meta.ingestion_log (
  ingestion_id UUID DEFAULT uuid(),
  dataset      VARCHAR NOT NULL,          -- 'enade'
  indicator    VARCHAR NOT NULL,          -- 'conceito_enade','cpc','idd','igc'
  ano_enade    INTEGER NOT NULL,
  source_path  VARCHAR NOT NULL,
  source_hash  VARCHAR,
  ingest_date  DATE DEFAULT CURRENT_DATE,
  status       VARCHAR DEFAULT 'SUCCESS',
  row_count    BIGINT,
  notes        VARCHAR,
  created_at   TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meta.quality_checks (
  qc_id        UUID DEFAULT uuid(),
  dataset      VARCHAR NOT NULL,
  layer        VARCHAR NOT NULL,          -- 'bronze'|'silver'|'gold'
  table_name   VARCHAR NOT NULL,
  ano_enade    INTEGER,
  check_name   VARCHAR NOT NULL,
  check_type   VARCHAR NOT NULL,
  check_result VARCHAR NOT NULL,          -- 'PASS'|'FAIL'|'WARN'
  failing_rows BIGINT,
  details      VARCHAR,
  checked_at   TIMESTAMP DEFAULT now()
);
```

---

### 2.2 Bronze (conforme headers reais)

#### Bronze — Conceito ENADE (curso-ano)

Baseado em `PLANILHA_ENADE`

```sql
CREATE TABLE IF NOT EXISTS bronze.conceito_enade (
  ano_enade INTEGER NOT NULL,
  ingest_date DATE DEFAULT CURRENT_DATE,
  source_file VARCHAR,

  -- Identificação
  ano INTEGER,
  co_area INTEGER,
  area_avaliacao VARCHAR,
  grau_academico VARCHAR,
  co_ies INTEGER,
  no_ies VARCHAR,
  sg_ies VARCHAR,
  organizacao_academica VARCHAR,
  categoria_administrativa VARCHAR,
  co_curso INTEGER,
  modalidade_ensino VARCHAR,
  co_municipio INTEGER,
  municipio_curso VARCHAR,
  sg_uf VARCHAR,

  -- Participação
  concluintes_inscritos INTEGER,
  concluintes_participantes INTEGER,

  -- Notas
  nota_bruta_fg DOUBLE,
  nota_padronizada_fg DOUBLE,
  nota_bruta_ce DOUBLE,
  nota_padronizada_ce DOUBLE,
  conceito_enade_continuo DOUBLE,
  conceito_enade_faixa INTEGER,

  created_at TIMESTAMP DEFAULT now()
);
```

#### Bronze — CPC (curso-ano)

Baseado em `CPC_2023`

```sql
CREATE TABLE IF NOT EXISTS bronze.cpc (
  ano_enade INTEGER NOT NULL,
  ingest_date DATE DEFAULT CURRENT_DATE,
  source_file VARCHAR,

  -- Identificação
  ano INTEGER,
  co_ies INTEGER,
  no_ies VARCHAR,
  sg_ies VARCHAR,
  organizacao_academica VARCHAR,
  categoria_administrativa VARCHAR,
  co_curso INTEGER,
  co_area INTEGER,
  area_avaliacao VARCHAR,
  modalidade_ensino VARCHAR,
  co_municipio INTEGER,
  municipio_curso VARCHAR,
  sg_uf VARCHAR,

  -- Participação / Enade
  concluintes_inscritos INTEGER,
  concluintes_participantes INTEGER,
  nota_bruta_fg DOUBLE,
  nota_padronizada_fg DOUBLE,
  nota_bruta_ce DOUBLE,
  nota_padronizada_ce DOUBLE,
  conceito_enade_continuo DOUBLE,

  -- Enem / IDD (componentes no arquivo CPC)
  concluintes_com_nota_enem INTEGER,
  prop_concluintes_com_nota_enem DOUBLE,
  nota_bruta_idd DOUBLE,
  nota_padronizada_idd DOUBLE,

  -- Componentes CPC
  nota_bruta_org_didatico_pedagogica DOUBLE,
  nota_padronizada_org_didatico_pedagogica DOUBLE,
  nota_bruta_infra DOUBLE,
  nota_padronizada_infra DOUBLE,
  nota_bruta_oaf DOUBLE,
  nota_padronizada_oaf DOUBLE,
  nota_bruta_mestres DOUBLE,
  nota_padronizada_mestres DOUBLE,
  nota_bruta_doutores DOUBLE,
  nota_padronizada_doutores DOUBLE,
  nota_bruta_regime_trabalho DOUBLE,
  nota_padronizada_regime_trabalho DOUBLE,

  cpc_continuo DOUBLE,
  cpc_faixa INTEGER,

  created_at TIMESTAMP DEFAULT now()
);
```

#### Bronze — IDD (curso-ano)

Baseado em `IDD_2023`

```sql
CREATE TABLE IF NOT EXISTS bronze.idd (
  ano_enade INTEGER NOT NULL,
  ingest_date DATE DEFAULT CURRENT_DATE,
  source_file VARCHAR,

  ano INTEGER,
  co_area INTEGER,
  area_avaliacao VARCHAR,
  co_ies INTEGER,
  no_ies VARCHAR,
  sg_ies VARCHAR,
  organizacao_academica VARCHAR,
  categoria_administrativa VARCHAR,
  co_curso INTEGER,
  modalidade_ensino VARCHAR,
  co_municipio INTEGER,
  municipio_curso VARCHAR,
  sg_uf VARCHAR,

  concluintes_inscritos INTEGER,
  concluintes_participantes INTEGER,
  concluintes_participantes_com_enem INTEGER,
  prop_participantes_com_enem DOUBLE,

  nota_bruta_idd DOUBLE,
  idd_continuo DOUBLE,
  idd_faixa INTEGER,

  created_at TIMESTAMP DEFAULT now()
);
```

#### Bronze — IGC (IES-ano) + abas auxiliares

IGC tem 3 abas em 2023 (e isso varia por ano), então guardamos em 3 tabelas bronze separadas.

```sql
CREATE TABLE IF NOT EXISTS bronze.igc (
  ano_enade INTEGER NOT NULL,
  ingest_date DATE DEFAULT CURRENT_DATE,
  source_file VARCHAR,

  ano INTEGER,
  co_ies INTEGER,
  no_ies VARCHAR,
  sg_ies VARCHAR,
  organizacao_academica VARCHAR,
  categoria_administrativa VARCHAR,
  sg_uf VARCHAR,

  n_cursos_cpc_trienio INTEGER,
  alfa_prop_graduacao DOUBLE,
  conceito_medio_graduacao DOUBLE,
  beta_prop_mestrado DOUBLE,
  conceito_medio_mestrado DOUBLE,
  gama_prop_doutorandos DOUBLE,
  conceito_medio_doutorado DOUBLE,
  igc_continuo DOUBLE,
  igc_faixa INTEGER,

  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.igc_matriculas_trienio (
  ingest_date DATE DEFAULT CURRENT_DATE,
  source_file VARCHAR,

  ano_edicao INTEGER,
  co_ies INTEGER,
  co_curso INTEGER,
  n_matriculas INTEGER,

  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.igc_programas_capes (
  ingest_date DATE DEFAULT CURRENT_DATE,
  source_file VARCHAR,

  co_ies INTEGER,
  co_programa VARCHAR,
  matriculados_mestrado INTEGER,
  nota_mestrado DOUBLE,
  matriculados_doutorado INTEGER,
  nota_doutorado DOUBLE,

  created_at TIMESTAMP DEFAULT now()
);
```

---

### 2.3 Silver (modelo conformado)

Aqui a gente “congela” o **contrato analítico**:

```sql
CREATE TABLE IF NOT EXISTS silver.dim_instituicao (
  co_ies INTEGER PRIMARY KEY,
  no_ies VARCHAR,
  sg_ies VARCHAR,
  organizacao_academica VARCHAR,
  categoria_administrativa VARCHAR,
  sg_uf VARCHAR,
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS silver.dim_curso (
  co_curso INTEGER PRIMARY KEY,
  co_ies INTEGER NOT NULL,
  co_area INTEGER,
  area_avaliacao VARCHAR,
  grau_academico VARCHAR,
  modalidade_ensino VARCHAR,
  co_municipio INTEGER,
  municipio_curso VARCHAR,
  sg_uf VARCHAR,
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS silver.fact_conceito_enade (
  ano_enade INTEGER NOT NULL,
  co_curso INTEGER NOT NULL,
  concluintes_inscritos INTEGER,
  concluintes_participantes INTEGER,
  nota_bruta_fg DOUBLE,
  nota_padronizada_fg DOUBLE,
  nota_bruta_ce DOUBLE,
  nota_padronizada_ce DOUBLE,
  conceito_enade_continuo DOUBLE,
  conceito_enade_faixa INTEGER,
  ingest_date DATE,
  PRIMARY KEY (ano_enade, co_curso)
);

CREATE TABLE IF NOT EXISTS silver.fact_cpc (
  ano_enade INTEGER NOT NULL,
  co_curso INTEGER NOT NULL,
  cpc_continuo DOUBLE,
  cpc_faixa INTEGER,
  -- componentes úteis
  nota_bruta_idd DOUBLE,
  nota_padronizada_idd DOUBLE,
  concluintes_com_nota_enem INTEGER,
  prop_concluintes_com_nota_enem DOUBLE,
  ingest_date DATE,
  PRIMARY KEY (ano_enade, co_curso)
);

CREATE TABLE IF NOT EXISTS silver.fact_idd (
  ano_enade INTEGER NOT NULL,
  co_curso INTEGER NOT NULL,
  idd_continuo DOUBLE,
  idd_faixa INTEGER,
  nota_bruta_idd DOUBLE,
  concluintes_participantes_com_enem INTEGER,
  prop_participantes_com_enem DOUBLE,
  ingest_date DATE,
  PRIMARY KEY (ano_enade, co_curso)
);

CREATE TABLE IF NOT EXISTS silver.fact_igc (
  ano_enade INTEGER NOT NULL,
  co_ies INTEGER NOT NULL,
  igc_continuo DOUBLE,
  igc_faixa INTEGER,
  n_cursos_cpc_trienio INTEGER,
  alfa_prop_graduacao DOUBLE,
  beta_prop_mestrado DOUBLE,
  gama_prop_doutorandos DOUBLE,
  ingest_date DATE,
  PRIMARY KEY (ano_enade, co_ies)
);
```

---

### 2.4 Gold (views prontas)

```sql
CREATE VIEW IF NOT EXISTS gold.course_quality_year AS
SELECT
  f.ano_enade,
  c.co_curso,
  c.co_ies,
  c.co_area,
  c.area_avaliacao,
  c.grau_academico,
  c.modalidade_ensino,
  c.sg_uf,
  c.municipio_curso,

  f.conceito_enade_faixa,
  f.conceito_enade_continuo,
  f.nota_padronizada_fg,
  f.nota_padronizada_ce,

  cp.cpc_faixa,
  cp.cpc_continuo,

  idd.idd_faixa,
  idd.idd_continuo

FROM silver.fact_conceito_enade f
JOIN silver.dim_curso c
  ON c.co_curso = f.co_curso
LEFT JOIN silver.fact_cpc cp
  ON cp.ano_enade = f.ano_enade AND cp.co_curso = f.co_curso
LEFT JOIN silver.fact_idd idd
  ON idd.ano_enade = f.ano_enade AND idd.co_curso = f.co_curso;

CREATE VIEW IF NOT EXISTS gold.ies_quality_year AS
SELECT
  i.ano_enade,
  d.co_ies,
  d.no_ies,
  d.sg_ies,
  d.organizacao_academica,
  d.categoria_administrativa,
  d.sg_uf,

  i.igc_faixa,
  i.igc_continuo,

  COUNT(DISTINCT g.co_curso) AS qtd_cursos_avaliados,
  AVG(CASE WHEN g.conceito_enade_faixa IN (4,5) THEN 1.0 ELSE 0.0 END) AS pct_cursos_faixa_4_5,
  AVG(CASE WHEN upper(g.modalidade_ensino) LIKE '%EAD%' THEN 1.0 ELSE 0.0 END) AS pct_cursos_ead
FROM silver.fact_igc i
JOIN silver.dim_instituicao d
  ON d.co_ies = i.co_ies
LEFT JOIN gold.course_quality_year g
  ON g.ano_enade = i.ano_enade AND g.co_ies = i.co_ies
GROUP BY ALL;
```

---

## 3) Duas decisões de governança para suportar “novos anos”

### ✅ Decisão 1 — “Contrato Silver fixo”

Os nomes e tipos da Silver **não mudam**.  
Se 2024/2025 vier com coluna a mais/menos na planilha, isso fica:

- ou na **Bronze** (camada permissiva),

- ou em uma coluna opcional na Silver (se fizer sentido analítico).

Isso evita quebrar dashboards e notebooks.

### ✅ Decisão 2 — “Aba Atualizações”

Você notou que vários anos têm aba “Atualizações” (2019, 2021, 2022 etc.).  
Boa prática: **capturar essa aba numa tabela `bronze.<indicador>_updates`** ou registrar no `meta.ingestion_log.notes`.  
Isso te dá rastreabilidade quando o INEP corrige dados.


