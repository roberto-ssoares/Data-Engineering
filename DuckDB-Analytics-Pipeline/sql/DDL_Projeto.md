# DDL DuckDB - Projeto

Arquitetura Medalhão é uma forma bem “engenharia” de escrever é:

- **Raw**: landing *imutável* (arquivo original, por ano).

- **Bronze**: *staging governado* (padronização mínima + metadados + checagens de qualidade + trilha de auditoria).

- **Silver**: dados **conformados** (modelo analítico coerente, chaves, normalização, comparabilidade).

- **Gold**: produtos analíticos (métricas, distribuições, tendências, “serving layer”).

A seguir vai o **DDL completo no DuckDB** (com schemas separados) já preparado para **atualização por novos anos**.

> **Como usar**: rode este SQL no seu `enade.duckdb` (ou `warehouse.duckdb`).  
> Depois a gente cria as queries de carga (ingestão e transforms).

```sql
-- =========================================================
-- 0) SCHEMAS (camadas)
-- =========================================================
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS meta;

-- =========================================================
-- 1) META / GOVERNANÇA (auditoria + qualidade + controle incremental)
-- =========================================================

-- 1.1. Controle de arquivos ingeridos (idempotência)
CREATE TABLE IF NOT EXISTS meta.ingestion_log (
  ingestion_id       UUID DEFAULT uuid(),
  dataset            VARCHAR NOT NULL,          -- ex: 'enade'
  indicator          VARCHAR NOT NULL,          -- ex: 'CPC','IGC','IDD','CONCEITO_ENADE'
  ano_enade          INTEGER NOT NULL,
  source_path        VARCHAR NOT NULL,
  source_hash        VARCHAR,                   -- opcional: hash do arquivo
  ingest_date        DATE DEFAULT CURRENT_DATE,
  status             VARCHAR DEFAULT 'SUCCESS', -- SUCCESS|FAILED|SKIPPED
  row_count          BIGINT,
  notes              VARCHAR,
  created_at         TIMESTAMP DEFAULT now()
);

-- 1.2. Resultados de checagens de qualidade
CREATE TABLE IF NOT EXISTS meta.quality_checks (
  qc_id              UUID DEFAULT uuid(),
  dataset            VARCHAR NOT NULL,          -- 'enade'
  layer              VARCHAR NOT NULL,          -- 'bronze'|'silver'|'gold'
  table_name         VARCHAR NOT NULL,
  ano_enade          INTEGER,
  check_name         VARCHAR NOT NULL,
  check_type         VARCHAR NOT NULL,          -- 'not_null','unique','range','domain','referential'
  check_result       VARCHAR NOT NULL,          -- 'PASS'|'FAIL'|'WARN'
  failing_rows       BIGINT,
  details            VARCHAR,
  checked_at         TIMESTAMP DEFAULT now()
);

-- 1.3. Controle do último ano processado (por indicador/camada)
CREATE TABLE IF NOT EXISTS meta.pipeline_state (
  dataset            VARCHAR NOT NULL,
  indicator          VARCHAR NOT NULL,
  last_bronze_year   INTEGER,
  last_silver_year   INTEGER,
  last_gold_year     INTEGER,
  updated_at         TIMESTAMP DEFAULT now(),
  PRIMARY KEY (dataset, indicator)
);

-- =========================================================
-- 2) BRONZE (staging governado)
--    Obs: Bronze é onde você coloca "mínimo necessário":
--    - ano_enade, ingest_date, source_file
--    - padronização de nomes/tipos básicos
-- =========================================================

-- 2.1. Conceito Enade (por curso)
CREATE TABLE IF NOT EXISTS bronze.conceito_enade (
  ano_enade                   INTEGER NOT NULL,
  ingest_date                 DATE DEFAULT CURRENT_DATE,
  source_file                 VARCHAR,

  -- Chaves / identificadores (nomes genéricos; mapeamos na carga)
  id_ies                       VARCHAR,
  id_curso                     VARCHAR,
  nome_ies                     VARCHAR,
  nome_curso                   VARCHAR,
  area_avaliacao               VARCHAR,
  grau_academico               VARCHAR,
  modalidade                   VARCHAR,
  uf                           VARCHAR,
  municipio                    VARCHAR,

  -- Medidas
  nota_formacao_geral          DOUBLE,
  nota_componente_especifico   DOUBLE,
  nota_geral                   DOUBLE,
  conceito_enade_faixa         INTEGER,  -- 1..5

  -- trilha
  created_at                   TIMESTAMP DEFAULT now()
);

-- 2.2. CPC (por curso)
CREATE TABLE IF NOT EXISTS bronze.cpc (
  ano_enade                   INTEGER NOT NULL,
  ingest_date                 DATE DEFAULT CURRENT_DATE,
  source_file                 VARCHAR,

  id_ies                       VARCHAR,
  id_curso                     VARCHAR,
  nome_ies                     VARCHAR,
  nome_curso                   VARCHAR,
  area_avaliacao               VARCHAR,
  grau_academico               VARCHAR,
  modalidade                   VARCHAR,
  uf                           VARCHAR,
  municipio                    VARCHAR,

  cpc_continuo                 DOUBLE,
  cpc_faixa                    INTEGER,  -- 1..5

  created_at                   TIMESTAMP DEFAULT now()
);

-- 2.3. IDD (por curso)
CREATE TABLE IF NOT EXISTS bronze.idd (
  ano_enade                   INTEGER NOT NULL,
  ingest_date                 DATE DEFAULT CURRENT_DATE,
  source_file                 VARCHAR,

  id_ies                       VARCHAR,
  id_curso                     VARCHAR,
  nome_ies                     VARCHAR,
  nome_curso                   VARCHAR,
  area_avaliacao               VARCHAR,
  grau_academico               VARCHAR,
  modalidade                   VARCHAR,
  uf                           VARCHAR,
  municipio                    VARCHAR,

  idd_valor                    DOUBLE,
  idd_faixa                    INTEGER,  -- se houver

  created_at                   TIMESTAMP DEFAULT now()
);

-- 2.4. IGC (por IES)
CREATE TABLE IF NOT EXISTS bronze.igc (
  ano_enade                   INTEGER NOT NULL,
  ingest_date                 DATE DEFAULT CURRENT_DATE,
  source_file                 VARCHAR,

  id_ies                       VARCHAR,
  nome_ies                     VARCHAR,
  categoria_administrativa     VARCHAR,
  organizacao_academica        VARCHAR,
  uf                           VARCHAR,
  municipio                    VARCHAR,

  igc_continuo                 DOUBLE,
  igc_faixa                    INTEGER,  -- 1..5

  created_at                   TIMESTAMP DEFAULT now()
);

-- =========================================================
-- 3) SILVER (dados conformados / modelo analítico)
-- =========================================================

-- 3.1. Dimensão Instituição (IES)
CREATE TABLE IF NOT EXISTS silver.dim_instituicao (
  id_ies                   VARCHAR PRIMARY KEY,
  nome_ies                 VARCHAR,
  categoria_administrativa VARCHAR,
  organizacao_academica    VARCHAR,
  uf                       VARCHAR,
  municipio                VARCHAR,
  updated_at               TIMESTAMP DEFAULT now()
);

-- 3.2. Dimensão Curso
CREATE TABLE IF NOT EXISTS silver.dim_curso (
  id_curso         VARCHAR PRIMARY KEY,
  id_ies           VARCHAR NOT NULL,
  nome_curso       VARCHAR,
  area_avaliacao   VARCHAR,
  grau_academico   VARCHAR,
  modalidade       VARCHAR,
  uf               VARCHAR,
  municipio        VARCHAR,
  updated_at       TIMESTAMP DEFAULT now()
);

-- 3.3. Fatos (por ano)
CREATE TABLE IF NOT EXISTS silver.fact_conceito_enade (
  ano_enade                 INTEGER NOT NULL,
  id_curso                  VARCHAR NOT NULL,
  nota_formacao_geral        DOUBLE,
  nota_componente_especifico DOUBLE,
  nota_geral                 DOUBLE,
  conceito_enade_faixa       INTEGER,
  ingest_date                DATE,
  PRIMARY KEY (ano_enade, id_curso)
);

CREATE TABLE IF NOT EXISTS silver.fact_cpc (
  ano_enade     INTEGER NOT NULL,
  id_curso      VARCHAR NOT NULL,
  cpc_continuo   DOUBLE,
  cpc_faixa      INTEGER,
  ingest_date    DATE,
  PRIMARY KEY (ano_enade, id_curso)
);

CREATE TABLE IF NOT EXISTS silver.fact_idd (
  ano_enade     INTEGER NOT NULL,
  id_curso      VARCHAR NOT NULL,
  idd_valor      DOUBLE,
  idd_faixa      INTEGER,
  ingest_date    DATE,
  PRIMARY KEY (ano_enade, id_curso)
);

CREATE TABLE IF NOT EXISTS silver.fact_igc (
  ano_enade     INTEGER NOT NULL,
  id_ies        VARCHAR NOT NULL,
  igc_continuo   DOUBLE,
  igc_faixa      INTEGER,
  ingest_date    DATE,
  PRIMARY KEY (ano_enade, id_ies)
);

-- =========================================================
-- 4) GOLD (produtos analíticos)
--    Sugestão prática: começar como VIEWs (rápido) e depois materializar.
-- =========================================================

-- 4.1. Núcleo por curso/ano (join conformado)
CREATE VIEW IF NOT EXISTS gold.gold_course_quality_year AS
SELECT
  ce.ano_enade,
  c.id_curso,
  c.id_ies,
  c.area_avaliacao,
  c.grau_academico,
  c.modalidade,
  c.uf,
  c.municipio,

  ce.conceito_enade_faixa,
  ce.nota_formacao_geral,
  ce.nota_componente_especifico,
  ce.nota_geral,

  cp.cpc_faixa,
  cp.cpc_continuo,

  idd.idd_faixa,
  idd.idd_valor,

  ce.ingest_date AS ingest_date_conceito,
  cp.ingest_date AS ingest_date_cpc,
  idd.ingest_date AS ingest_date_idd
FROM silver.fact_conceito_enade ce
JOIN silver.dim_curso c
  ON c.id_curso = ce.id_curso
LEFT JOIN silver.fact_cpc cp
  ON cp.ano_enade = ce.ano_enade AND cp.id_curso = ce.id_curso
LEFT JOIN silver.fact_idd idd
  ON idd.ano_enade = ce.ano_enade AND idd.id_curso = ce.id_curso;

-- 4.2. Visão institucional por ano
CREATE VIEW IF NOT EXISTS gold.gold_ies_quality_year AS
SELECT
  i.ano_enade,
  inst.id_ies,
  inst.nome_ies,
  inst.categoria_administrativa,
  inst.organizacao_academica,
  inst.uf,
  inst.municipio,

  i.igc_faixa,
  i.igc_continuo,

  COUNT(DISTINCT g.id_curso) AS qtd_cursos_avaliados,
  AVG(CASE WHEN g.conceito_enade_faixa IN (4,5) THEN 1.0 ELSE 0.0 END) AS pct_cursos_faixa_4_5,
  AVG(CASE WHEN g.modalidade ILIKE '%EAD%' THEN 1.0 ELSE 0.0 END) AS pct_cursos_ead
FROM silver.fact_igc i
JOIN silver.dim_instituicao inst
  ON inst.id_ies = i.id_ies
LEFT JOIN gold.gold_course_quality_year g
  ON g.ano_enade = i.ano_enade AND g.id_ies = i.id_ies
GROUP BY ALL;

-- 4.3. Distribuição de faixas por segmento (exemplo: UF e Modalidade)
CREATE VIEW IF NOT EXISTS gold.gold_distribution_conceito_by_uf_modalidade AS
SELECT
  ano_enade,
  uf,
  modalidade,
  COUNT(*) AS n_cursos,
  AVG(CASE WHEN conceito_enade_faixa = 1 THEN 1.0 ELSE 0.0 END) AS pct_faixa_1,
  AVG(CASE WHEN conceito_enade_faixa = 2 THEN 1.0 ELSE 0.0 END) AS pct_faixa_2,
  AVG(CASE WHEN conceito_enade_faixa = 3 THEN 1.0 ELSE 0.0 END) AS pct_faixa_3,
  AVG(CASE WHEN conceito_enade_faixa = 4 THEN 1.0 ELSE 0.0 END) AS pct_faixa_4,
  AVG(CASE WHEN conceito_enade_faixa = 5 THEN 1.0 ELSE 0.0 END) AS pct_faixa_5,
  AVG(CASE WHEN conceito_enade_faixa IN (4,5) THEN 1.0 ELSE 0.0 END) AS pct_faixa_4_5
FROM gold.gold_course_quality_year
GROUP BY ALL;

-- 4.4. Tendência por curso (evolução)
CREATE VIEW IF NOT EXISTS gold.gold_trend_course AS
SELECT
  id_curso,
  id_ies,
  MIN(ano_enade) AS first_year,
  MAX(ano_enade) AS last_year,
  COUNT(*)       AS n_years_observed,
  (MAX(conceito_enade_faixa) - MIN(conceito_enade_faixa)) AS trend_conceito,
  (MAX(cpc_faixa) - MIN(cpc_faixa)) AS trend_cpc
FROM gold.gold_course_quality_year
GROUP BY ALL;
```

## A inclusão da Bronze muda a DDL (e melhora o projeto)

Ela muda porque agora você tem **duas preocupações adicionais**:

1. **Rastreabilidade**: `source_file`, `ingest_date`, `ingestion_log`

2. **Qualidade**: registrar checks em `meta.quality_checks`

Isso é “cara de produção”.
