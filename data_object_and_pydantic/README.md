# Dataclass vs Pydantic V2: Architectural Blueprint & Practical Workflow

A practical, runnable learning repository designed for **Mid-to-Senior Developers and Software Architects** to master the differences, trade-offs, performance characteristics, and clean architectural boundaries between Python standard library `@dataclass` and Pydantic V2 (`BaseModel`).

---

## 🏛️ Architectural Comparison Matrix

| Concern | Standard `@dataclass` | Pydantic V2 `BaseModel` | Architectural Recommendation |
| :--- | :--- | :--- | :--- |
| **Type Annotations** | Static tooling only (Mypy, Pyright) | Runtime validation & type enforcement | Use Dataclass internally; Pydantic at network boundary |
| **Input Coercion** | **No** (Stores raw types passed at runtime) | **Yes** (Coerces string `"100"` $\to$ `int 100`, `"2025-01-01"` $\to$ `date`) | Pydantic for untrusted raw JSON/HTTP inputs |
| **Field Constraints** | Manual imperatively in `__post_init__` | Declarative via `Field()`, `@field_validator`, `@model_validator` | Pydantic for rich API input contracts & constraints |
| **JSON & Schemas** | Manual via `asdict()` + custom encoders | Native `model_dump()`, `model_dump_json()`, `model_json_schema()` | Pydantic for JSON serialization/deserialization |
| **OpenAPI Integration**| Limited / indirect (wrapped by FastAPI) | Native & rich (Field docs, regex patterns, bounds) | Pydantic for FastAPI Request/Response DTOs |
| **Arbitrary Objects** | **Natural** (Holds DB pools, Locks, Clients) | **Requires special handling** (`arbitrary_types_allowed=True`) | Dataclass for Domain Entities, Repositories, & Services |
| **External Dependency**| Standard Library (`dataclasses`) | Third-party dependency (`pydantic`) | Dataclass for core domain models to avoid lock-in |
| **Best Role** | **Internal domain records, entities & service wiring** | **Data / trust boundaries (API DTOs, Config, Message Payloads)** | Clean architecture separation: DTOs $\leftrightarrow$ Domain Entities |

---

## 📁 Repository Structure & Executable Modules

All scripts in this directory are fully functional and self-contained. Run any module directly or run the automated test suite.

```text
data_object_and_pydantic/
├── README.md                                   # This architectural guide & debugging manual
├── __init__.py                                 # Package marker
├── ex01_type_annotations_and_coercion.py       # Static type hints vs runtime validation & coercion
├── ex02_field_constraints_and_validation.py    # __post_init__ vs Field(), validators, & validate_assignment
├── ex03_json_serialization_and_schemas.py      # asdict() vs model_dump_json(), aliasing & JSON Schema
├── ex04_fastapi_openapi_integration.py         # FastAPI route handling & OpenAPI spec differences
├── ex05_domain_services_and_arbitrary_objects.py # Stateful service wiring & un-serializable handles
├── ex06_performance_and_benchmarks.py          # Micro-benchmarks (ops/sec) & memory footprint (sys.getsizeof)
├── app.py                                      # Production FastAPI app showcasing Clean Layered Architecture
└── tests/
    ├── __init__.py
    ├── test_comparisons.py                     # Unit test suite verifying behaviors
    └── test_fastapi_app.py                     # Integration test suite using FastAPI TestClient
```

---

## 🏃 Running the Code & Test Suite

### Execute Executable Modules:
Run any module directly from the repository root:

```bash
PYTHONPATH=. python3 data_object_and_pydantic/ex01_type_annotations_and_coercion.py
PYTHONPATH=. python3 data_object_and_pydantic/ex02_field_constraints_and_validation.py
PYTHONPATH=. python3 data_object_and_pydantic/ex03_json_serialization_and_schemas.py
PYTHONPATH=. python3 data_object_and_pydantic/ex04_fastapi_openapi_integration.py
PYTHONPATH=. python3 data_object_and_pydantic/ex05_domain_services_and_arbitrary_objects.py
PYTHONPATH=. python3 data_object_and_pydantic/ex06_performance_and_benchmarks.py
```

### Run the FastAPI App with Uvicorn:
```bash
PYTHONPATH=. uvicorn data_object_and_pydantic.app:app --reload
```
Access interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.

### Run Test Suite:
```bash
PYTHONPATH=. pytest data_object_and_pydantic/tests
```

---

## 🐛 Interactive Debugging Guide & Breakpoint Pointers

Each script contains explicit `# 🐛 DEBUGPOINT: ...` annotations to guide deep inspection under VS Code, PyCharm, or PDB debuggers.

### Module 1: `ex01_type_annotations_and_coercion.py`
- **DEBUGPOINT 1** (`Dataclass`): Set breakpoint after instantiating `invalid_dc`.
  - **Inspect**: `invalid_dc.__dict__`. Notice `invalid_dc.user_id` is still `'999'` (string) and `invalid_dc.birth_date` is still `'1995-10-20'` (string). No coercion took place.
- **DEBUGPOINT 2** (`Pydantic Lax`): Set breakpoint after instantiating `pydantic_user`.
  - **Inspect**: `pydantic_user.user_id` (coerced to `int`), `pydantic_user.birth_date` (coerced to `datetime.date(1995, 10, 20)`).
- **DEBUGPOINT 3** (`Pydantic Validation Error`): Set breakpoint inside `except ValidationError as e:` block.
  - **Inspect**: `e.errors()`. Observe the structured list of error dictionaries containing `loc`, `msg`, and `type`.

### Module 2: `ex02_field_constraints_and_validation.py`
- **DEBUGPOINT 1** (`__post_init__`): Set breakpoint inside `DataclassOrder.__post_init__()`.
  - **Inspect**: `self.quantity` and `self.unit_price` during imperative validation execution.
- **DEBUGPOINT 2** (`@field_validator`): Set breakpoint inside `validate_order_id_prefix()`.
  - **Inspect**: `value` parameter before returning transformed result.
- **DEBUGPOINT 4** (`validate_assignment`): Set breakpoint after `p_order.quantity = -50`.
  - **Inspect**: Catch block and verify that `p_order.quantity` retains its previous valid state (`10`).

### Module 3: `ex03_json_serialization_and_schemas.py`
- **DEBUGPOINT 1** (`asdict() TypeError`): Break inside `except TypeError as err:`.
  - **Inspect**: `err`. Standard `json.dumps(asdict(invoice))` fails because UUID, Decimal, and datetime are not natively JSON serializable.
- **DEBUGPOINT 3** (`model_dump_json`): Set breakpoint before `p_invoice.model_dump_json()`.
  - **Inspect**: Returned JSON string. Pydantic handles UUIDs, Decimals, Enums, and ISO dates out of the box.

### Module 4: `ex04_fastapi_openapi_integration.py`
- **DEBUGPOINT 1 & 2** (`FastAPI Handlers`): Set breakpoint inside `create_dataclass_user` and `create_pydantic_user`.
  - **Inspect**: `payload` type and attributes. Notice how FastAPI wraps both models for endpoint parameter binding.
- **Inspect OpenAPI Spec**: Evaluate `client.get("/openapi.json").json()` to see constraints (`minLength`, `pattern`, `maximum`) present in Pydantic schema vs minimal Dataclass schema.

### Module 5: `ex05_domain_services_and_arbitrary_objects.py`
- **DEBUGPOINT 1** (`Domain Service Wiring`): Set breakpoint inside `DataclassUserRepository.fetch_user_by_id`.
  - **Inspect**: `self.connection` (holding un-serializable `sqlite3` connection & `threading.Lock`).
- **DEBUGPOINT 2** (`Pydantic Schema Error`): Set breakpoint inside `except PydanticSchemaGenerationError`.
  - **Inspect**: Pydantic's refusal to build a model around raw un-serializable C-extension handles unless `arbitrary_types_allowed=True` is explicitly toggled.

### Module 6: `ex06_performance_and_benchmarks.py`
- **DEBUGPOINT 1** (`Memory Footprint`): Set breakpoint after size calculation.
  - **Inspect**: `sys.getsizeof()` comparison:
    - Standard Dataclass + `__dict__`: ~152 bytes
    - Slotted Dataclass (`slots=True`): ~64 bytes
    - Pydantic BaseModel + `__dict__`: ~256 bytes

---

## 🎯 Clean Architecture Recommendation for Devs & Architects

1. **Use Pydantic at the Trust Boundaries (Network / Transport Layer)**:
   - FastAPI Request & Response DTOs
   - Configuration Management (`pydantic-settings`)
   - Incoming Message Queue (Kafka, RabbitMQ, SQS) payload parsing
2. **Use Dataclasses (`slots=True`) in the Core Domain Layer**:
   - Internal Business Entities & Aggregates
   - Stateful Domain Services, Repositories, DB Connection Wiring
   - High-throughput in-memory data processing loops (100,000+ items)
3. **Map explicitly between DTOs and Domain Entities**:
   - Keeps business logic free of third-party framework dependencies.
   - Prevents API contract changes from leaking into internal core domain models.
