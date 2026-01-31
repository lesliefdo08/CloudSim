# CloudSim Backend

Production-ready FastAPI backend for CloudSim - AWS-like cloud simulator.

## Architecture

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management (env-based)
├── database.py          # Database session management
├── dependencies.py      # FastAPI dependencies
│
├── api/                 # API routes (versioned)
│   ├── v1/
│   │   ├── auth.py      # Authentication endpoints
│   │   ├── instances.py # EC2 instances endpoints
│   │   ├── vpcs.py      # VPC endpoints
│   │   └── volumes.py   # EBS volumes endpoints
│   └── router.py        # Router registration
│
├── core/                # Core utilities
│   ├── exceptions.py    # Custom exceptions
│   ├── resource_ids.py  # AWS ID generation (i-*, vpc-*, vol-*)
│   └── security.py      # Authentication & authorization
│
├── middleware/          # Custom middleware
│   ├── auth.py          # JWT authentication
│   ├── error_handler.py # Global error handling
│   └── logging.py       # Request logging
│
├── models/              # SQLAlchemy models
│   ├── base.py          # Base model class
│   ├── user.py          # User model
│   ├── instance.py      # EC2 instance model
│   ├── vpc.py           # VPC model
│   └── volume.py        # EBS volume model
│
├── schemas/             # Pydantic schemas
│   ├── common.py        # Common schemas (pagination, errors)
│   ├── user.py          # User schemas
│   ├── instance.py      # Instance schemas
│   └── error.py         # Error response schemas
│
├── services/            # Business logic
│   ├── auth_service.py  # Authentication logic
│   ├── ec2_service.py   # EC2 business logic
│   └── iam_service.py   # IAM business logic
│
├── workers/             # Celery background tasks
│   ├── celery_app.py    # Celery configuration
│   └── tasks.py         # Background tasks
│
└── utils/               # Helper utilities
    ├── arn.py           # ARN generation & parsing
    └── pagination.py    # Pagination helpers
```

## Conventions

### Resource IDs

All resources follow AWS naming conventions:

- **EC2 Instances**: `i-<17-char-hex>` (e.g., `i-0f1ac123456789abc`)
- **EBS Volumes**: `vol-<17-char-hex>` (e.g., `vol-abc123def456789`)
- **VPCs**: `vpc-<8-char-hex>` (e.g., `vpc-1a2b3c4d`)
- **Subnets**: `subnet-<8-char-hex>` (e.g., `subnet-5e6f7g8h`)
- **Security Groups**: `sg-<17-char-hex>` (e.g., `sg-0123456789abcdef`)
- **AMIs**: `ami-<17-char-hex>` (e.g., `ami-0abcdef123456789`)
- **Access Keys**: `AKIA<16-char-upper>` (e.g., `AKIAIOSFODNN7EXAMPLE`)

### ARNs (Amazon Resource Names)

Format: `arn:partition:service:region:account-id:resource-type/resource-id`

Examples:
```
arn:aws:ec2:us-east-1:123456789012:instance/i-0123456789
arn:aws:s3:::my-bucket
arn:aws:iam::123456789012:user/alice
```

### Error Handling

All errors follow AWS error response format:

```json
{
  "error": {
    "code": "ResourceNotFound",
    "message": "Instance 'i-0123456789' not found"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

Common error codes:
- `AuthenticationFailure`: Authentication failed
- `UnauthorizedOperation`: Not authorized
- `ResourceNotFound`: Resource doesn't exist
- `InvalidParameterValue`: Invalid parameter
- `ResourceLimitExceeded`: Service limit reached
- `InternalError`: Internal service error

### Pagination

All list endpoints support pagination:

**Request**:
```
GET /api/v1/instances?page=1&page_size=20
```

**Response**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### API Versioning

- Current version: `/api/v1/`
- All endpoints are versioned
- Future versions: `/api/v2/`, etc.

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker 24+

### Installation

1. Install dependencies:
```bash
poetry install
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your configuration

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

### Development

Run with auto-reload:
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
poetry run pytest
```

### Code Quality

Format code:
```bash
poetry run black app/
```

Lint code:
```bash
poetry run ruff app/
```

Type checking:
```bash
poetry run mypy app/
```

## API Documentation

When running in debug mode, interactive API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-31T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "docker": "healthy"
  }
}
```

## Production Deployment

### Environment Variables

All configuration is managed through environment variables. See `.env.example` for required variables.

**Critical for Production**:
- Set `DEBUG=false`
- Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
- Configure proper `DATABASE_URL` with SSL
- Set appropriate `CORS_ORIGINS`
- Enable monitoring with `ENABLE_METRICS=true`

### Database Migrations

Always use Alembic for schema changes:

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Background Workers

Start Celery workers for background tasks:

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

## Next Steps

This is the foundation. To implement features:

1. **Create Models**: Add SQLAlchemy models in `app/models/`
2. **Create Schemas**: Add Pydantic schemas in `app/schemas/`
3. **Create Services**: Add business logic in `app/services/`
4. **Create Routes**: Add API endpoints in `app/api/v1/`
5. **Register Routes**: Import and register in `app/api/router.py`

Example flow for EC2 instances:
1. `models/instance.py` - Database model
2. `schemas/instance.py` - Request/response schemas
3. `services/ec2_service.py` - Business logic
4. `api/v1/instances.py` - API endpoints
5. Register in `api/router.py`

Stop here. Feature implementation comes next.
