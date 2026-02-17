# OpenStack VM Lifecycle Management API

A RESTful API for managing OpenStack virtual machine lifecycle operations, built with FastAPI, SQLAlchemy, and the OpenStack SDK.

[![CI](https://github.com/zac-amd/openstack-vm-api/actions/workflows/ci.yml/badge.svg)](https://github.com/zac-amd/openstack-vm-api/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- **VM Lifecycle Management**: Create, list, get, update, and delete VMs
- **VM Actions**: Start, stop, reboot (soft/hard), and sync state
- **Resource Management**: List available flavors and images
- **API Key Authentication**: Secure endpoint access
- **OpenStack Integration**: Real OpenStack SDK or mock mode for testing
- **Async Architecture**: Built with async/await for high performance
- **Auto-generated Documentation**: Swagger UI and ReDoc
- **Containerized**: Docker and Docker Compose support
- **CI/CD Ready**: GitHub Actions workflow included

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Architecture](#architecture)
- [Contributing](#contributing)

## 🏃 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/zac-amd/openstack-vm-api.git
cd openstack-vm-api

# Start with Docker Compose (mock mode)
docker-compose up -d

# API is now available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### Local Development

```bash
# Clone and install
git clone https://github.com/zac-amd/openstack-vm-api.git
cd openstack-vm-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
uvicorn app.main:app --reload
```

## 📦 Installation

### Prerequisites

- Python 3.10+
- pip
- Docker & Docker Compose (optional)

### Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (includes testing tools)
pip install -e ".[dev]"
```

## ⚙️ Configuration

Configuration is managed through environment variables. Copy `.env.example` to `.env` and update:

```bash
# API Configuration
API_TITLE=OpenStack VM Lifecycle API
API_VERSION=1.0.0
DEBUG=false

# API Key Authentication
API_KEY=your-secure-api-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./openstack_vm.db

# OpenStack Mode
USE_MOCK_OPENSTACK=true  # Set to false for real OpenStack

# OpenStack Credentials (when USE_MOCK_OPENSTACK=false)
OS_AUTH_URL=https://your-openstack:5000/v3
OS_PROJECT_NAME=your-project
OS_USERNAME=your-username
OS_PASSWORD=your-password
OS_USER_DOMAIN_NAME=Default
OS_PROJECT_DOMAIN_NAME=Default
OS_REGION_NAME=RegionOne
```

## 📚 API Reference

### Authentication

All endpoints (except `/health` and `/`) require an API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/vms
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/` | API information |
| **Virtual Machines** | | |
| POST | `/api/v1/vms` | Create a new VM |
| GET | `/api/v1/vms` | List all VMs (paginated) |
| GET | `/api/v1/vms/{uuid}` | Get VM details |
| PATCH | `/api/v1/vms/{uuid}` | Update VM |
| DELETE | `/api/v1/vms/{uuid}` | Delete VM |
| POST | `/api/v1/vms/{uuid}/start` | Start VM |
| POST | `/api/v1/vms/{uuid}/stop` | Stop VM |
| POST | `/api/v1/vms/{uuid}/reboot` | Reboot VM |
| POST | `/api/v1/vms/{uuid}/sync` | Sync VM state from OpenStack |
| **Flavors** | | |
| GET | `/api/v1/flavors` | List available flavors |
| GET | `/api/v1/flavors/{id}` | Get flavor details |
| **Images** | | |
| GET | `/api/v1/images` | List available images |
| GET | `/api/v1/images/{id}` | Get image details |

### Example: Create a VM

```bash
curl -X POST http://localhost:8000/api/v1/vms \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-web-server",
    "flavor_id": "m1.small",
    "image_id": "ubuntu-22.04",
    "description": "Web server instance"
  }'
```

### Example: VM Lifecycle Operations

```bash
# Stop a VM
curl -X POST http://localhost:8000/api/v1/vms/{uuid}/stop \
  -H "X-API-Key: your-api-key"

# Start a VM
curl -X POST http://localhost:8000/api/v1/vms/{uuid}/start \
  -H "X-API-Key: your-api-key"

# Reboot a VM (soft)
curl -X POST http://localhost:8000/api/v1/vms/{uuid}/reboot \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"reboot_type": "SOFT"}'
```

## 📁 Project Structure

```
openstack-vm-api/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD pipeline
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # API v1 router combining all endpoints
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── flavors.py     # Flavor endpoints (list, get)
│   │           ├── health.py      # Health check endpoint
│   │           ├── images.py      # Image endpoints (list, get)
│   │           └── vms.py         # VM lifecycle endpoints (CRUD + actions)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py          # Custom exception classes
│   │   ├── openstack_client.py    # OpenStack SDK wrapper (mock + real)
│   │   └── security.py            # API key authentication
│   ├── models/
│   │   ├── __init__.py
│   │   └── vm.py                  # SQLAlchemy VM model with state machine
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py              # Shared schemas (health, errors, flavors, images)
│   │   └── vm.py                  # VM request/response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── vm_service.py          # VM business logic layer
│   ├── __init__.py
│   ├── config.py                  # Pydantic settings configuration
│   ├── database.py                # Async SQLAlchemy database setup
│   └── main.py                    # FastAPI application entry point
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures and configuration
│   └── test_api_endpoints.py      # API integration tests
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore patterns
├── ARCHITECTURE.md                # Architecture documentation
├── docker-compose.yml             # Docker Compose configuration
├── Dockerfile                     # Multi-stage Docker build
├── LICENSE                        # MIT License
├── Makefile                       # Development commands
├── pyproject.toml                 # Python project configuration
├── README.md                      # This file
├── requirements.txt               # Python dependencies
└── ROADMAP.md                     # Future features backlog
```

## 🛠️ Development

### Using Make Commands

```bash
# Show available commands
make help

# Install dependencies
make install

# Run development server
make run

# Run tests
make test

# Format code
make format

# Lint code
make lint
```

### Code Style

```bash
# Format code with Black
black app/ tests/

# Lint with Ruff
ruff check app/ tests/

# Type checking with MyPy
mypy app/
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_endpoints.py -v
```

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t openstack-vm-api:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e API_KEY=your-secure-key \
  -e USE_MOCK_OPENSTACK=false \
  -e OS_AUTH_URL=https://openstack:5000/v3 \
  openstack-vm-api:latest
```

### Docker Compose

```bash
# Production with environment variables
export API_KEY=your-secure-key
export USE_MOCK_OPENSTACK=false
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📐 Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation including:

- System design and component diagrams
- Design patterns (Repository, Service Layer, Strategy, State Machine)
- Database schema design
- VM state machine transitions
- Security architecture
- Technology choices and trade-offs
- Scalability considerations

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and enhancements:

- **Phase 2**: JWT authentication, RBAC, audit logging
- **Phase 3**: PostgreSQL, Redis caching, Celery tasks
- **Phase 4**: VM snapshots, floating IPs, Prometheus metrics
- **Phase 5**: Multi-cloud support, Terraform provider

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Support

- Documentation: http://localhost:8000/docs (when running locally)
- Issues: https://github.com/zac-amd/openstack-vm-api/issues
- Repository: https://github.com/zac-amd/openstack-vm-api

---

Built with ❤️ using [FastAPI](https://fastapi.tiangolo.com/) and [OpenStack SDK](https://docs.openstack.org/openstacksdk/)
