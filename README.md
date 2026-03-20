# RevfySegment

App full-stack para upload de CSV com dados de clientes e geração automática de campanhas de marketing segmentadas.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React 19, TypeScript, Axios
- **Background:** Threading (alternativa leve ao Celery para SQLite)
- **Real-time:** SSE (Server-Sent Events)
- **Infra:** Docker Compose

## Como rodar

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### Sem Docker

```bash
# backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm start
```

### Testes

```bash
cd backend && pytest tests/ -v
```

Tem um `sample_data.csv` (20 rows) e `sample_data_large.csv` (200 rows) na raiz pra testar upload.

## Arquitetura

```text
backend/app/
  main.py           → FastAPI + CORS + error handlers
  models.py         → Upload, User, Campaign, campaign_users (M:N)
  routers/          → upload, campaigns, users
  services/         → csv_validator, campaign_service, sse_manager
  middleware/       → rate_limit (sliding window, 5 req/min por IP)
  schemas/          → Pydantic models + PaginatedResponse[T]

frontend/src/
  types/            → interfaces TS separadas por domínio
  api.ts            → axios client + SSE helper
  components/       → UploadPage, CampaignsPage, CampaignDetailPage, UsersPage
```

### Fluxo

1. Upload CSV → POST /upload valida row-by-row → retorna 201 com erros
2. Thread em background gera campanhas (só users daquele upload)
3. Frontend recebe status em tempo real via SSE
4. Campaigns e Users ficam disponíveis pra consulta paginada

## Decisões e trade-offs

**SQLite vs PostgreSQL** — Escolhi SQLite pra simplificar o setup. Uma command (`docker compose up`) e tudo roda. Em produção usaria Postgres.

**Threading vs Celery** — SQLite não suporta bem concorrência pesada, então threading é suficiente e evita dependência de Redis/RabbitMQ. A thread cria sua própria session pra evitar conflitos do SQLAlchemy.

**SSE vs Polling** — Comunicação é unidirecional (server → client), então SSE é mais leve que WebSocket e tem reconexão automática no browser via EventSource.

**`original_id` separado** — O `id` do CSV é salvo como `original_id`. O banco usa auto-increment próprio. Evita conflito de PK entre uploads diferentes.

## Estratégia de uploads duplicados

**Criar novo** — cada upload gera registros independentes. Não sobrescreve nem rejeita duplicatas.

Por quê:
- Simples e previsível
- Sem risco de perder dados de imports anteriores
- Permite comparar versões diferentes do mesmo arquivo
- Geração de campanhas é idempotente por upload (deleta e recria se rodar de novo)

## Regras de segmentação

| Campanha | Regra |
| -------- | ----- |
| Starter | age < 30 AND income < 3000 |
| Growth | 30 ≤ age ≤ 50 AND 3000 ≤ income ≤ 10000 |
| Premium | age > 50 OR income > 10000 |
| High Value Youth | age < 30 AND income > 5000 |

Um user pode estar em mais de uma campanha (relação N:N via `campaign_users`).

## Endpoints

| Método | Rota | Descrição |
| ------ | ---- | --------- |
| POST | /upload | Upload CSV (rate limited: 5/min) |
| GET | /upload/{id}/status | Status do processamento |
| GET | /upload/{id}/stream | SSE real-time |
| GET | /campaigns | Listar campanhas (paginado, filtro `upload_id`) |
| GET | /campaigns/{id} | Detalhe + users paginados |
| GET | /users | Listar users (paginado, filtros: name, age, income) |

Paginação padrão: `?page=1&page_size=20` (max 100). Erros sempre no formato `{error, message, details}`.

## Bonus

- Docker Compose com healthcheck
- Swagger/OpenAPI auto-gerado com descrições
- Rate limiting no upload (5/min por IP, sliding window)
- SSE pra status updates em tempo real

## Limitações

- SQLite não escala pra escrita concorrente → usar Postgres em prod
- Rate limiter e SSE são in-memory → precisaria Redis pra múltiplas instâncias
- Sem autenticação
