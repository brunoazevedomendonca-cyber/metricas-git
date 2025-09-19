# Git Metrics Dashboard

Dashboard web para acompanhar métricas de performance do time através de commits Git.

## Setup

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Configurar GitHub Token:**
   - Gere um token no GitHub: Settings > Developer settings > Personal access tokens
   - Edite `config.json` e adicione seu token e repositórios

3. **Coletar dados iniciais:**
```bash
python data_collector.py
```

4. **Executar aplicação:**
```bash
python app.py
```

5. **Acessar:** http://localhost:5000

## Configuração Automática (Cron)

Para coleta automática diária:
```bash
# Adicionar ao crontab
0 6 * * * cd /path/to/project && python data_collector.py
```

## Métricas Disponíveis

- **Commits por desenvolvedor** (por período/repo)
- **Pull Requests** (quantidade e tempo de merge)
- **Releases** (quantidade por repo)
- **Exportação CSV** de todos os dados

## Estrutura

- `data_collector.py` - Coleta dados do GitHub
- `app.py` - Aplicação Flask
- `config.json` - Configuração de repos e token
- `templates/` - Interface web
- `metrics.db` - Banco SQLite (criado automaticamente)
