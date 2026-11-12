"""
04_fastapi_openapi_integration.py

Demonstrates:
1. FastAPI endpoint integration with standard dataclass vs Pydantic BaseModel.
2. Direct request parsing, query parameters, request body handling.
3. Under-the-hood FastAPI schema generation for both models.
4. Native OpenAPI schema inspection.

Target Audience: Mid/Senior Devs & Architects
"""

from dataclasses import dataclass, field
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field


app = FastAPI(
    title="Dataclass vs Pydantic OpenAPI Integration Demo",
    version="1.0.0",
    description="Interactive demonstration comparing FastAPI handling of stdlib @dataclass vs Pydantic BaseModel."
)


# ============================================================================
# 1. STANDARD DATACLASS ROUTE MODEL
# ============================================================================

@dataclass
class DataclassUserRequest:
    username: str
    age: int
    tags: List[str] = field(default_factory=list)


@dataclass
class DataclassUserResponse:
    user_id: int
    username: str
    is_adult: bool
    tags: List[str]


@app.post("/api/dataclass-user", response_model=DataclassUserResponse, tags=["Dataclass Endpoints"])
def create_dataclass_user(payload: DataclassUserRequest):
    """
    FastAPI endpoint accepting standard @dataclass as Request Body.
    FastAPI internally builds a Pydantic metadata schema around @dataclass to parse JSON body.
    """
    # 🐛 DEBUGPOINT 1: Place a breakpoint inside this route handler!
    # Inspect type(payload) -> <class 'DataclassUserRequest'>
    # Inspect payload.username, payload.age, payload.tags
    is_adult = payload.age >= 18
    return DataclassUserResponse(
        user_id=4041,
        username=payload.username,
        is_adult=is_adult,
        tags=payload.tags
    )


# ============================================================================
# 2. PYDANTIC BASEMODEL ROUTE MODEL
# ============================================================================

class PydanticUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    age: int = Field(..., ge=1, le=120)
    tags: List[str] = Field(default_factory=list, max_length=5)


class PydanticUserResponse(BaseModel):
    user_id: int
    username: str
    is_adult: bool
    tags: List[str]


@app.post("/api/pydantic-user", response_model=PydanticUserResponse, status_code=status.HTTP_201_CREATED, tags=["Pydantic Endpoints"])
def create_pydantic_user(payload: PydanticUserRequest):
    """
    FastAPI endpoint accepting Pydantic BaseModel with full declarative validations & rich OpenAPI descriptions.
    """
    # 🐛 DEBUGPOINT 2: Place a breakpoint inside this route handler!
    # Inspect type(payload) -> <class 'PydanticUserRequest'>
    # Notice payload has already passed all Field constraints (min_length, age bounds, pattern)!
    is_adult = payload.age >= 18
    return PydanticUserResponse(
        user_id=7072,
        username=payload.username,
        is_adult=is_adult,
        tags=payload.tags
    )


# ============================================================================
# 3. INTERACTIVE DEMONSTRATION & OPENAPI INSPECTION
# ============================================================================

def run_openapi_integration_demo():
    print("\n" + "=" * 80)
    print("FASTAPI & OPENAPI INTEGRATION DEMO: DATACLASS vs PYDANTIC")
    print("=" * 80)

    client = TestClient(app)

    # 1. Test Dataclass endpoint with valid input
    dc_res = client.post("/api/dataclass-user", json={"username": "mario", "age": "25", "tags": ["hero"]})
    print(f"[Dataclass Endpoint Valid Request Status]: {dc_res.status_code}")
    print(f"  Response Body: {dc_res.json()}")

    # 2. Test Pydantic endpoint with invalid input (username too short & age > 120)
    py_err_res = client.post("/api/pydantic-user", json={"username": "ab", "age": 150})
    print(f"\n[Pydantic Endpoint Invalid Request Status]: {py_err_res.status_code}")
    print("  Validation Error Detail Excerpt:")
    for err in py_err_res.json().get("detail", []):
        print(f"   -> Field '{'.'.join(str(x) for x in err['loc'])}': {err['msg']}")

    # 3. OpenAPI Schema comparison inspection
    print("\n" + "-" * 60)
    print("OPENAPI SCHEMA GENERATION COMPARISON")
    print("-" * 60)

    openapi_schema = client.get("/openapi.json").json()
    schemas = openapi_schema.get("components", {}).get("schemas", {})

    print(f"Generated Schemas in OpenAPI spec: {list(schemas.keys())}\n")

    dc_schema = schemas.get("DataclassUserRequest", {})
    py_schema = schemas.get("PydanticUserRequest", {})

    print("[Dataclass OpenAPI Request Schema]:")
    print(f"  Properties: {list(dc_schema.get('properties', {}).keys())}")
    print(f"  Required: {dc_schema.get('required')}")

    print("\n[Pydantic OpenAPI Request Schema (Rich Constraints Included)]:")
    print(f"  Properties: {list(py_schema.get('properties', {}).keys())}")
    for fname, props in py_schema.get("properties", {}).items():
        constraints = {k: v for k, v in props.items() if k in ("minLength", "maxLength", "minimum", "maximum", "pattern")}
        print(f"   - Field '{fname}': constraints={constraints}")


if __name__ == "__main__":
    run_openapi_integration_demo()
