# 🧠 CHEAT-SHEET MENTAL — ENGENHARIA DE DADOS (ENTREVISTAS)

Use como **mapa de pensamento**, não como script.

---

## 🔷 1. ESTRUTURA-MÃE (serve para 70% das perguntas)

Sempre responda em **3 camadas**:

> **O quê → Por quê → Como**

Exemplo mental:

- **O quê:** o que o pipeline faz

- **Por quê:** risco que evita / valor que entrega

- **Como:** implementação concreta

⚠️ Se inverter (como → o quê), a resposta soa júnior.

---

## 🔷 2. ARQUITETURA BRONZE / SILVER / GOLD (mantra)

Grave assim:

```
Raw → contrato
Bronze → estrutura
Silver → significado
Gold → valor
```

Frase pronta:

> “Raw preserva, Bronze organiza, Silver interpreta, Gold entrega valor.”

---

## 🔷 3. DECISÕES ARQUITETURAIS (checklist rápido)

Sempre que perguntarem “por que X?” pense:

- 🔁 Reprocessamento

- 🔍 Auditabilidade

- 🧩 Desacoplamento

- 📈 Escalabilidade

Se sua resposta tocar **pelo menos dois**, é madura.

---

## 🔷 4. PIPELINE ROBUSTO (resposta-âncora)

Sempre mencione **3 garantias**:

1. Idempotência

2. Observabilidade

3. Falha explícita

Frase forte:

> “Pipeline confiável não é o que roda, é o que produz dado verificável.”

---

## 🔷 5. DEBUG EM PRODUÇÃO (roteiro fixo)

Quando perguntarem “o que você faz se der erro”:

```
Logs → _SUCCESS → Snapshot → Reprocessar camada
```

Nunca diga:

- “Olho direto no banco”

- “Corrijo manualmente”

---

## 🔷 6. DATA QUALITY (onde e por quê)

Memorize:

- Bronze → estrutura mínima

- Silver → regras semânticas

- Gold → contratos de consumo

Frase curta:

> “Qualidade cresce conforme o dado ganha significado.”

---

## 🔷 7. PANDAS vs SPARK (resposta elegante)

Nunca diga “pandas não escala”.

Diga:

> “A lógica é independente do engine. O que muda é paralelismo e execução.”

Estrutura:

- Conceito igual

- Execução diferente

- Arquitetura preservada

---

## 🔷 8. GOLD EM CAMADAS (pergunta clássica)

Memorize este triângulo:

```
Exploração → Analytics → Produção
```

Ou:

- Gold Basic → analista

- Gold Analytics → BI

- Gold Advanced → plataforma

---

## 🔷 9. SCHEMA DRIFT (resposta madura)

Checklist mental:

- Valido mínimo

- Tolerante a extras

- Falho rápido se contrato quebra

Frase pronta:

> “Aceito mudança, mas não aceito quebra silenciosa.”

---

## 🔷 10. ERRO CLÁSSICO (e como responder)

Pergunta:

> “Por que não usar logo Great Expectations?”

Resposta mental:

- Escopo

- Maturidade

- Evolução natural

Nunca diga:

- “Não tive tempo”

- “Não conheço”

---

## 🔷 11. FRASE-ÂNCORA DE SENIORIDADE (use 1 ou 2)

Guarde algumas:

- “Tecnologia muda, arquitetura permanece.”

- “Negócio muda mais rápido que dado bruto.”

- “Falha parcial não pode derrubar valor total.”

- “Formato é detalhe, contrato é o essencial.”

Use com moderação.

---

## 🔷 12. RESPOSTA FINAL (quando quiser fechar forte)

Sempre termine assim:

> “Esse projeto foi pensado para crescer sem refatoração estrutural.”

Isso sinaliza visão de longo prazo.

---

## 🎯 COMO TREINAR (5 minutos por dia)

1. Escolha **1 pergunta**

2. Responda em voz alta usando:
   
   - O quê
   
   - Por quê
   
   - Como

3. Encaixe **1 frase-âncora**

4. Pare antes de se alongar

---


