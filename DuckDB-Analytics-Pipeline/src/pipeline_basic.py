import duckdb
import pandas as pd

con = duckdb.connect("analytics.duckdb")

# Exemplo simples
df = pd.DataFrame({
    "categoria": ["A", "A", "B", "B"],
    "valor": [10, 20, 30, 40]
})

con.register("raw_data", df)

con.execute("""
    CREATE OR REPLACE TABLE analytics AS
    SELECT
        categoria,
        SUM(valor) AS total_valor
    FROM raw_data
    GROUP BY categoria
""")

print(con.execute("SELECT * FROM analytics").fetchdf())
