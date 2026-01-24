# Jumla-bot Backend

Production-grade backend for real estate lead management and automation platform.

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL 15+ (async SQLAlchemy + Alembic)
- **Task Queue**: Celery + Redis
- **Storage**: S3-compatible (AWS S3 / MinIO)
- **LLM**: OpenAI / Anthropic (adapter pattern)
- **Messaging**: Twilio (SMS) + SendGrid (Email)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### 1. Clone Repository

```bash
git clone https://github.com/your-org/jumla-bot-backend.git
cd jumla-bot-backend
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys:
# - OPENAI_API_KEY
# - TWILIO credentials
# - SENDGRID_API_KEY
```

### 3. Start Services with Docker Compose

```bash
# Start all services (db, redis, minio, backend, worker)
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

Services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery Monitor)**: http://localhost:5555
- **MinIO Console**: http://localhost:9001

### 4. Run Database Migrations

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
alembic upgrade head

# Exit container
exit
```

### 5. Seed Sample Data

```bash
# Seed database with 8 sample leads
docker-compose exec backend python scripts/seed_data.py
```

**Test credentials:**
- Admin: `admin@demo-rei.com` / `Admin123!`
- Agent: `agent@demo-rei.com` / `Agent123!`

### 6. Test the API

```bash
# Get access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@demo-rei.com", "password": "Admin123!"}'

# Use token to list leads
curl http://localhost:8000/api/v1/leads \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Or visit http://localhost:8000/docs for interactive API documentation.

---

## Development Setup (without Docker)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
```

### 2. Start Required Services

```bash
# Start PostgreSQL (using Docker)
docker run -d \
  --name jumla-postgres \
  -e POSTGRES_DB=jumla_bot \
  -e POSTGRES_USER=jumla_user \
  -e POSTGRES_PASSWORD=jumla_password \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis
docker run -d \
  --name jumla-redis \
  -p 6379:6379 \
  redis:7-alpine

# Start MinIO
docker run -d \
  --name jumla-minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin123 \
  -p 9000:9000 \
  -p 9001:9001 \
  minio/minio server /data --console-address ":9001"
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start Development Server

```bash
# Terminal 1: API server
uvicorn app.main:app --reload --port 8000

# Terminal 2: Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduled tasks)
celery -A app.tasks.celery_app beat --loglevel=info
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_offer_engine.py

# Run with verbose output
pytest -v tests/
```

**Coverage target**: >= 80% for business-critical modules (offer engine, scoring engine, enrichment).

---

## Code Quality

```bash
# Format code
black .
isort .

# Lint
flake8 app tests --max-line-length=120

# Type checking
mypy app --ignore-missing-imports
```

---

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

---

## Project Structure

```
jumla-bot-backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration
│   ├── dependencies.py         # Shared dependencies
│   ├── api/v1/                 # API routers
│   │   ├── auth.py
│   │   ├── leads.py
│   │   ├── conversations.py
│   │   ├── offers.py
│   │   └── ...
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   │   ├── llm_client.py       # LLM adapter
│   │   ├── offer_engine.py     # Offer calculations
│   │   ├── scoring_engine.py   # Lead scoring
│   │   └── ...
│   ├── tasks/                  # Celery tasks
│   └── core/                   # Core utilities
│       ├── database.py
│       ├── security.py
│       └── logging.py
├── alembic/                    # Database migrations
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## API Documentation

Full API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

**Authentication**
- `POST /api/v1/auth/login` - Login and get JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

**Leads**
- `POST /api/v1/leads` - Create new lead
- `GET /api/v1/leads` - List leads (with filters)
- `GET /api/v1/leads/{id}` - Get lead details
- `PATCH /api/v1/leads/{id}` - Update lead

**Conversations**
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/lead/{id}` - Get conversation history

**Offers**
- `POST /api/v1/offers` - Create offer
- `POST /api/v1/offers/{id}/approve` - Approve offer (admin)
- `POST /api/v1/offers/{id}/send` - Send offer to lead

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT signing key (32+ chars) | `your-secret-key-here` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | `...` |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | `+1234567890` |
| `SENDGRID_API_KEY` | SendGrid API key | `SG....` |
| `SENDGRID_FROM_EMAIL` | Sender email address | `noreply@yourdomain.com` |
| `S3_ACCESS_KEY_ID` | S3 access key | `minioadmin` |
| `S3_SECRET_ACCESS_KEY` | S3 secret key | `minioadmin123` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key (fallback) | None |
| `S3_ENDPOINT_URL` | S3 endpoint (for MinIO) | None |
| `ENVIRONMENT` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

See `.env.example` for full list.

---

## Architecture Decisions

### LLM Usage Policy

**CRITICAL**: LLM is used ONLY for:
- Extracting structured data from messages
- Generating conversational responses
- Summarizing information

**LLM NEVER**:
- Makes business decisions (pricing, offers, scoring)
- Deterministically computes values
- Controls workflow logic

All business logic is in **deterministic, testable functions**:
- `offer_engine.py` - 100% deterministic offer calculations
- `scoring_engine.py` - 100% deterministic lead scoring

### Idempotency

All Celery tasks are designed to be idempotent:
- Tasks use unique identifiers (lead_id, task_id)
- Database operations are UPDATE-or-INSERT
- Safe to retry on failure

### Security

- **Authentication**: JWT tokens (access + refresh)
- **Authorization**: RBAC with role-based permissions
- **Passwords**: bcrypt hashing
- **API Keys**: Environment variables only
- **CORS**: Configurable origins
- **Rate Limiting**: TODO (add in production)

---

## Troubleshooting

### Database connection failed

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker-compose logs db
```

### Celery tasks not running

```bash
# Check worker logs
docker-compose logs worker

# Check Redis connection
redis-cli ping
```

### LLM extraction failures

- Check API keys in `.env`
- Verify account has credits
- Check logs for specific error messages

### Port already in use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

---

## Production Deployment

### Security Checklist

- [ ] Generate strong `JWT_SECRET_KEY` (32+ characters)
- [ ] Use production database (not default credentials)
- [ ] Enable HTTPS only
- [ ] Set `DEBUG=false`
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting
- [ ] Enable Sentry or error tracking
- [ ] Use secrets manager (AWS Secrets Manager, etc.)
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Enable API authentication on all endpoints
- [ ] Review and update `CORS_ORIGINS`

### Infrastructure

- Use managed PostgreSQL (AWS RDS, Cloud SQL, etc.)
- Use managed Redis (ElastiCache, Cloud Memorystore, etc.)
- Use AWS S3 for storage (not MinIO)
- Run backend on container orchestration (ECS, Kubernetes, etc.)
- Set up autoscaling for workers
- Configure health checks
- Set up monitoring (Datadog, New Relic, etc.)

---

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests for new functionality
3. Ensure tests pass: `pytest`
4. Format code: `black . && isort .`
5. Commit: `git commit -m "feat: add your feature"`
6. Push: `git push origin feature/your-feature`
7. Create Pull Request

---

## License

Proprietary - All rights reserved

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/jumla-bot-backend/issues
- Email: dev@yourdomain.com