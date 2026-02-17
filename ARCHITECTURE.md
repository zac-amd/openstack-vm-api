# Architecture Documentation

This document describes the architecture, design decisions, and patterns used in the OpenStack VM Lifecycle Management API.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Design Patterns](#design-patterns)
4. [Component Details](#component-details)
5. [Database Design](#database-design)
6. [VM State Machine](#vm-state-machine)
7. [Security Architecture](#security-architecture)
8. [Technology Choices](#technology-choices)
9. [Scalability Considerations](#scalability-considerations)
10. [Trade-offs](#trade-offs)

---

## System Overview

The OpenStack VM Lifecycle Management API is a RESTful service that provides an abstraction layer over OpenStack's compute (Nova) API. It enables users to manage virtual machines through a simplified, well-documented API.

### Key Characteristics

- **Async-first**: Built with Python's async/await for non-blocking I/O
- **Layered Architecture**: Clean separation between API, service, and data layers
- **Pluggable Backend**: Supports both real OpenStack and mock mode
- **Stateless API**: State stored in database, enabling horizontal scaling

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Clients                                    │
│              (Web Apps, CLI Tools, Other Services)                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   FastAPI   │  │    CORS     │  │  API Key    │                  │
│  │   Router    │  │ Middleware  │  │    Auth     │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API Endpoints Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │     VMs     │  │   Flavors   │  │   Images    │  │   Health   │  │
│  │  Endpoints  │  │  Endpoints  │  │  Endpoints  │  │  Endpoint  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Service Layer                                │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                        VM Service                            │    │
│  │   • Business Logic    • State Validation   • Error Handling │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                          │                    │
                          ▼                    ▼
┌──────────────────────────────┐  ┌──────────────────────────────────┐
│       Data Access Layer       │  │     OpenStack Client Layer       │
│  ┌─────────────────────────┐  │  │  ┌─────────────────────────┐    │
│  │     SQLAlchemy ORM      │  │  │  │   Base Client (ABC)     │    │
│  │     (Async Session)     │  │  │  └─────────────────────────┘    │
│  └─────────────────────────┘  │  │           │          │          │
│              │                │  │           ▼          ▼          │
│              ▼                │  │  ┌────────────┐ ┌────────────┐  │
│  ┌─────────────────────────┐  │  │  │   Mock     │ │   Real     │  │
│  │   SQLite / PostgreSQL   │  │  │  │  Client    │ │  Client    │  │
│  └─────────────────────────┘  │  │  └────────────┘ └────────────┘  │
└──────────────────────────────┘  └──────────────────────────────────┘
                                                      │
                                                      ▼
                                  ┌──────────────────────────────────┐
                                  │          OpenStack API           │
                                  │    (Nova, Glance, Neutron)       │
                                  └──────────────────────────────────┘
```

---

## Design Patterns

### 1. Repository Pattern

The data access layer uses the Repository pattern to abstract database operations:

```python
# Service layer uses repository for data access
async def get_vm(self, vm_uuid: str) -> VMResponse:
    vm = await self._get_vm_by_uuid(vm_uuid)  # Repository method
    return VMResponse.model_validate(vm)
```

**Benefits:**
- Decouples business logic from data access
- Easier to test (mock repository)
- Can switch database implementations

### 2. Service Layer Pattern

Business logic is encapsulated in the service layer:

```python
class VMService:
    def __init__(self, session: AsyncSession, openstack_client: BaseOpenStackClient):
        self.session = session
        self.openstack = openstack_client

    async def create_vm(self, vm_data: VMCreate) -> VMResponse:
        # Validation, business logic, orchestration
        ...
```

**Benefits:**
- Separates concerns
- Reusable business logic
- Easier unit testing

### 3. Dependency Injection

FastAPI's `Depends()` for loose coupling:

```python
@router.post("/vms")
async def create_vm(
    vm_data: VMCreate,
    service: VMServiceDep,  # Injected
    api_key: APIKeyDep,      # Injected
) -> VMResponse:
    return await service.create_vm(vm_data)
```

**Benefits:**
- Testable components
- Swappable implementations
- Clear dependencies

### 4. Strategy Pattern

OpenStack client implementation:

```python
class BaseOpenStackClient(ABC):
    @abstractmethod
    async def create_server(self, ...) -> dict: pass

class MockOpenStackClient(BaseOpenStackClient):
    async def create_server(self, ...) -> dict:
        # Mock implementation

class RealOpenStackClient(BaseOpenStackClient):
    async def create_server(self, ...) -> dict:
        # Real OpenStack SDK calls
```

**Benefits:**
- Runtime backend selection
- Testing without real OpenStack
- Easy to add new backends

### 5. State Machine Pattern

VM lifecycle states:

```python
class VMState(str, Enum):
    BUILDING = "BUILDING"
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"
    ...

@property
def can_start(self) -> bool:
    return self.state in VMState.stopped_states()
```

**Benefits:**
- Enforces valid state transitions
- Self-documenting state logic
- Prevents invalid operations

---

## Component Details

### API Layer (`app/api/`)

- **Endpoints**: HTTP handlers, request/response handling
- **Router**: Route registration and versioning
- **Dependencies**: Authentication, database session

### Core Layer (`app/core/`)

- **Security**: API key authentication
- **Exceptions**: Custom exception hierarchy
- **OpenStack Client**: Abstraction over OpenStack SDK

### Models Layer (`app/models/`)

- **VM Model**: SQLAlchemy model with state machine
- **Base**: Declarative base for all models

### Schemas Layer (`app/schemas/`)

- **Request Schemas**: Input validation (Pydantic)
- **Response Schemas**: Output serialization
- **Common Schemas**: Shared schemas (errors, health)

### Services Layer (`app/services/`)

- **VM Service**: Business logic orchestration
- Coordinates between database and OpenStack

---

## Database Design

### VM Table Schema

```sql
CREATE TABLE vms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    openstack_id VARCHAR(36) UNIQUE,
    
    -- Configuration
    flavor_id VARCHAR(36) NOT NULL,
    image_id VARCHAR(36) NOT NULL,
    
    -- State
    state VARCHAR(20) NOT NULL DEFAULT 'BUILDING',
    state_description TEXT,
    
    -- Network
    ip_address VARCHAR(45),
    floating_ip VARCHAR(45),
    
    -- Resources (denormalized)
    vcpus INTEGER,
    memory_mb INTEGER,
    disk_gb INTEGER,
    
    -- Metadata
    description TEXT,
    user_data TEXT,
    key_name VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    launched_at TIMESTAMP,
    terminated_at TIMESTAMP
);

CREATE INDEX idx_vms_uuid ON vms(uuid);
CREATE INDEX idx_vms_state ON vms(state);
CREATE INDEX idx_vms_name ON vms(name);
CREATE INDEX idx_vms_openstack_id ON vms(openstack_id);
```

### Design Decisions

1. **UUID as External ID**: Internal auto-increment ID, external UUID for API
2. **Denormalized Resources**: Store vcpus/memory/disk for quick access without flavor lookup
3. **State Description**: Free-text field for error messages or status details
4. **Soft Delete**: VMs marked as DELETED rather than physically removed

---

## VM State Machine

```
                         ┌─────────────┐
              ┌──────────│  BUILDING   │
              │          └──────┬──────┘
              │                 │ success
              │                 ▼
              │          ┌─────────────┐
    error     │    ┌────►│   ACTIVE    │◄────┐
              │    │     └──────┬──────┘     │
              │    │            │            │
              │    │     ┌──────┴──────┐     │
              │    │     │             │     │
              │    │     ▼             ▼     │
              │    │  ┌──────┐    ┌────────┐ │
              │    │  │REBOOT│    │  STOP  │ │
              │    │  └──┬───┘    └────┬───┘ │
              │    │     │             │     │
              │    └─────┘             ▼     │
              │                  ┌─────────┐ │
              │                  │ SHUTOFF │─┘
              │                  └────┬────┘  START
              │                       │
              ▼                       ▼
         ┌─────────┐           ┌───────────┐
         │  ERROR  │           │  DELETED  │
         └─────────┘           └───────────┘
```

### State Transitions

| Current State | Action | Next State |
|---------------|--------|------------|
| BUILDING | success | ACTIVE |
| BUILDING | error | ERROR |
| ACTIVE | stop | SHUTOFF |
| ACTIVE | reboot | REBOOT → ACTIVE |
| ACTIVE | delete | DELETED |
| SHUTOFF | start | ACTIVE |
| SHUTOFF | delete | DELETED |
| ERROR | delete | DELETED |

---

## Security Architecture

### Authentication Flow

```
Client Request
      │
      ▼
┌─────────────────┐
│ X-API-Key Header│
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────┐
│ verify_api_key  │────►│ Return 401  │ (missing/invalid)
│   Dependency    │     └─────────────┘
└────────┬────────┘
         │ valid
         ▼
┌─────────────────┐
│  Proceed with   │
│    Request      │
└─────────────────┘
```

### Security Measures

1. **API Key Authentication**: Required for all protected endpoints
2. **Input Validation**: Pydantic schemas validate all inputs
3. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
4. **CORS Configuration**: Configurable allowed origins
5. **Non-root Container**: Docker container runs as non-root user
6. **Secret Management**: Environment variables for sensitive data

### Future Security Enhancements

- JWT tokens with user roles
- Rate limiting
- Request signing
- Audit logging

---

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | FastAPI | Async, auto-docs, type hints, high performance |
| **ORM** | SQLAlchemy 2.0 | Industry standard, async support, type hints |
| **Validation** | Pydantic | Built into FastAPI, excellent validation |
| **OpenStack SDK** | openstacksdk | Official SDK, well-maintained |
| **Database** | SQLite/PostgreSQL | SQLite for dev, Postgres for production |
| **Async Driver** | aiosqlite | Async SQLite support |
| **Testing** | pytest + httpx | Async testing, fixtures |
| **Container** | Docker | Standard containerization |
| **CI/CD** | GitHub Actions | Integrated, free for public repos |

---

## Scalability Considerations

### Horizontal Scaling

```
                    ┌─────────────┐
                    │   Load      │
                    │  Balancer   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
     ┌───────────┐   ┌───────────┐   ┌───────────┐
     │  API #1   │   │  API #2   │   │  API #3   │
     └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  PostgreSQL │
                    │   (Shared)  │
                    └─────────────┘
```

### Scaling Strategies

1. **Stateless API**: All state in database
2. **Connection Pooling**: SQLAlchemy async session management
3. **Caching** (future): Redis for frequently accessed data
4. **Async Operations**: Long operations via task queue

### Bottlenecks & Mitigations

| Bottleneck | Mitigation |
|------------|------------|
| Database connections | Connection pooling, read replicas |
| OpenStack API limits | Caching, rate limiting |
| Long-running operations | Background tasks (Celery) |

---

## Trade-offs

### 1. Mock vs Real OpenStack

**Decision**: Support both with runtime switching

**Trade-off**:
- ✅ Easy testing without infrastructure
- ✅ Development without OpenStack access
- ❌ Mock may not reflect real behavior
- ❌ Additional code complexity

### 2. SQLite vs PostgreSQL

**Decision**: SQLite default, PostgreSQL supported

**Trade-off**:
- ✅ Zero configuration for development
- ✅ Single file database
- ❌ Limited concurrent writes
- ❌ Less production-grade features

### 3. API Key vs JWT

**Decision**: API Key for simplicity

**Trade-off**:
- ✅ Simple implementation
- ✅ Easy to understand and use
- ❌ No user identity/roles
- ❌ No token expiration

### 4. Sync vs Async OpenStack Calls

**Decision**: Async wrapper over sync SDK

**Trade-off**:
- ✅ Non-blocking API
- ✅ Better resource utilization
- ❌ OpenStack SDK is synchronous
- ❌ May need thread pool for heavy loads

---

## Future Architecture Considerations

1. **Event-Driven**: Publish state changes to message queue
2. **CQRS**: Separate read/write models for scale
3. **Multi-tenancy**: User isolation and quotas
4. **Observability**: Distributed tracing, metrics
5. **Service Mesh**: Kubernetes with Istio/Linkerd
