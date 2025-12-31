# Data Engineering – Portfolio

Este repositório concentra meus **projetos práticos de Engenharia de Dados**, com foco em **pipelines, arquitetura de dados, reprodutibilidade e boas práticas orientadas à produção**.

Os projetos aqui demonstram como estruturar, implementar e evoluir pipelines de dados reais, indo desde ingestão robusta até datasets analíticos prontos para consumo por BI e Analytics.



## 🧱 Principais Conceitos Demonstrados

- Arquitetura de Data Lake (Bronze / Silver / Gold)
- Pipelines batch em Python
- Ingestão robusta de dados (encoding, delimitadores, falhas)
- Padronização, limpeza e enriquecimento de dados
- Modelagem analítica (fatos e dimensões)
- Particionamento de dados
- Logging estruturado
- Ambientes reprodutíveis (.venv)
- Código modular e orientado a pipelines



## 📂 Projetos

### 🔹 P01 – Data Lake (Bronze / Silver / Gold)

**Descrição:**  
Implementação de um Data Lake completo seguindo o padrão **Bronze → Silver → Gold**, com pipelines progressivos que demonstram desde transformações básicas até práticas orientadas à produção.

**Destaques:**

- Ingestão robusta de dados CSV
- Transformações defensivas
- Três níveis de Gold (Basic, Analytics, Advanced)
- Modelagem dimensional
- Dados particionados por ano/mês

📁 Caminho:

Data-Lake/P01-Bronze-Silver-Gold/



## 🚀 Tecnologias Utilizadas

- Python
- pandas
- Estrutura extensível para PySpark
- Conceitos aplicáveis a AWS (S3, Glue, Athena)
- Git / GitHub



## 🎯 Objetivo do Repositório

Este repositório foi criado com foco em **portfólio profissional**, alinhado com desafios reais enfrentados por Engenheiros de Dados em ambientes corporativos.

Ele complementa meus projetos de **Ciência de Dados**, mantendo uma separação clara entre análise/modelagem e engenharia/pipelines.


## 📌 Próximos Projetos (Roadmap)

- Orquestração com Apache Airflow
- Versão distribuída com PySpark
- Data Quality (Pandera / Great Expectations)
- Integração com serviços AWS
