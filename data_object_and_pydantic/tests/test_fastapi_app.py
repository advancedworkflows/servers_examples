"""
test_fastapi_app.py

Integration test suite for the FastAPI application (app.py):
1. Verifying API trust boundary endpoint (/api/v1/orders).
2. Request DTO validation errors (422 Unprocessable Entity).
3. Direct dataclass endpoint handling.
4. Side-by-side JSON schema comparison endpoint.

Target Audience: Mid/Senior Devs & Architects
"""

from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from data_object_and_pydantic.app import app


client = TestClient(app)


def test_create_order_success():
    """Verify posting a valid order through Pydantic DTO to Dataclass domain logic."""
    payload = {
        "customer": {
            "customer_id": str(uuid4()),
            "name": "Sarah Connor",
            "email": "sarah@skynet-resistance.org"
        },
        "items": [
            {
                "product_code": "PRD-101",
                "quantity": 2,
                "unit_price": 49.99
            },
            {
                "product_code": "PRD-202",
                "quantity": 1,
                "unit_price": 100.00
            }
        ]
    }

    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PROCESSED"
    assert data["item_count"] == 2
    assert data["total_amount"] == 199.98
    assert "order_id" in data


def test_create_order_validation_failure_bad_email_and_quantity():
    """Verify Pydantic trust boundary rejects invalid email and negative quantity with HTTP 422."""
    payload = {
        "customer": {
            "customer_id": str(uuid4()),
            "name": "Sarah Connor",
            "email": "not-an-email"  # Invalid format
        },
        "items": [
            {
                "product_code": "prd-101",  # Invalid regex (lowercase)
                "quantity": -5,            # Invalid quantity <= 0
                "unit_price": 10.0
            }
        ]
    }

    response = client.post("/api/v1/orders", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) >= 3


def test_direct_dataclass_endpoint():
    """Verify endpoint taking stdlib @dataclass as payload directly."""
    response = client.post("/api/v1/direct-dataclass", json={"title": "Audit Security Rules", "priority": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Audit Security Rules"
    assert data["priority"] == 2


def test_comparison_schema_endpoint():
    """Verify comparison schema endpoint returns Pydantic JSON schema."""
    response = client.get("/api/v1/comparison-schema")
    assert response.status_code == 200
    data = response.json()
    assert "pydantic_dto_schema" in data
    assert data["pydantic_dto_schema"]["title"] == "CreateOrderRequestDTO"
