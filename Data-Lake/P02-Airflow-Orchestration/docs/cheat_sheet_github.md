# Cheat Sheet — GitHub (Upload + Sincronização)

Objetivo: ter um guia rápido e confiável para:

- publicar um projeto local no GitHub (primeiro upload)
- manter sincronização (pull/push) sem dor
- trabalhar com branches e tags
- evitar subir arquivos indevidos (.venv, logs, datasets grandes)

> Ambiente típico: Windows + PowerShell, projeto em D:...

---

## 0) Pré-requisitos (1 minuto)

Verificar se o Git está instalado:



```powershell
git --version
```

Verificar usuário/email (importante para commits):

```powershell
git config --global user.name
git config --global user.email
```

Se precisar configurar:

```powershell
git config --global user.name "Roberto Soares"
git config --global user.email "seu-email@exemplo.com"
```

---

## 1) Primeiro upload (projeto local → GitHub)

### 1.1 Entrar na pasta do projeto

```powershell
cd D:\_DE-Projects\Data-Engineering\Data-Lake\P01-Bronze-Silver-Gold
```

### 1.2 Inicializar repositório (se ainda não existir)

```powershell
git init
```

### 1.3 Criar/ajustar .gitignore (essencial)

Exemplo mínimo recomendado para projetos Python + data:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# venv
.venv/
venv/
.env/

# Jupyter
.ipynb_checkpoints/

# Logs / runtime
logs/
*.log

# Data (decida o que versionar)
data/raw/
data/bronze/
data/silver/
data/gold/
data/gold_analytics/
data/gold_advanced/

# OS
.DS_Store
Thumbs.db
```

> Regra: versionar apenas dados pequenos de exemplo (ou um arquivo README explicando como obter os dados).

### 1.4 Primeiro commit

```powershell
git add .
git commit -m "Initial commit: project structure and pipelines"
```

### 1.5 Conectar ao repositório remoto (GitHub)

No GitHub, crie um repo vazio (sem README).  
Depois:

```powershell
git branch -M main
git remote add origin https://github.com/<seu-usuario>/<seu-repo>.git
git push -u origin main
```

Pronto: projeto publicado.

---

## 2) Fluxo diário (sincronização padrão)

### 2.1 Antes de trabalhar: atualizar do remoto

```powershell
git pull
```

### 2.2 Durante o trabalho: ver status

```powershell
git status
```

### 2.3 Commitar mudanças com mensagem objetiva

```powershell
git add .
git commit -m "Fix: enforce absolute project paths for Airflow execution"
```

### 2.4 Enviar para o GitHub

```powershell
git push
```

---

## 3) Trabalhando com branches (recomendado)

Criar uma branch para uma feature/correção:

```powershell
git checkout -b fix/airflow-paths
```

Depois de commits:

```powershell
git push -u origin fix/airflow-paths
```

Voltar para main:

```powershell
git checkout main
git pull
```

Mesclar branch na main (local):

```powershell
git merge fix/airflow-paths
git push
```

---

## 4) Tags e versões (Release)

Quando fechar uma fase (ex.: P02 estável):

```powershell
git tag -a v0.2.0 -m "P02 stable: wrappers + success markers + force flags"
git push origin v0.2.0
```

---

## 5) Corrigir “subi arquivo que não devia”

### 5.1 Parar de versionar um arquivo/pasta já rastreado

Exemplo: você adicionou `data/` sem querer.

1. Ajuste o `.gitignore`

2. Remova do tracking (sem apagar do disco):

```powershell
git rm -r --cached data
git commit -m "Chore: stop tracking data directory"
git push
```

---

## 6) Repositório já existe no GitHub e quero baixar (clone)

```powershell
cd D:\_DE-Projects
git clone https://github.com/<seu-usuario>/<seu-repo>.git
```

---

## 7) Conflitos (pull deu conflito)

1. Ver arquivos conflitantes:

```powershell
git status
```

2. Abrir arquivo, resolver manualmente os marcadores `<<<<<<`, `======`, `>>>>>>`

3. Marcar como resolvido e finalizar:

```powershell
git add .
git commit -m "Resolve merge conflicts"
git push
```

---

## 8) Comandos de diagnóstico (rápidos)

Ver remotes:

```powershell
git remote -v
```

Ver histórico:

```powershell
git log --oneline --decorate -n 20
```

Ver diferenças antes do commit:

```powershell
git diff
```

Ver branch atual:

```powershell
git branch
```

---

## 9) Boas práticas (para portfólio)

- Commits pequenos e com intenção clara (Fix/Feat/Docs/Chore).

- README forte + docs/ bem organizados.

- Nunca versionar `.venv`, logs e datasets grandes.

- Marcar versões com tags (v0.1.0, v0.2.0...).

- Criar Issues no GitHub para documentar problemas e soluções.

---

## 10) Template de mensagens de commit (copia e cola)

- `Feat: add silver_to_gold_analytics pipeline`

- `Fix: run wrappers with cwd=/opt/p01 and PYTHONPATH`

- `Fix: prevent empty _SUCCESS when no output files`

- `Docs: add architecture diagram and operational checklist`

- `Chore: clean docker volumes and compose overrides`

---


