"""
test_comparisons.py

Unit test suite verifying the key architectural differences between standard dataclasses and Pydantic models:
1. Type coercion & runtime validation.
2. Field constraints & cross-field validation.
3. Serialization & JSON encoding.
4. Arbitrary object handling.

Target Audience: Mid/Senior Devs & Architects
"""

from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError

from data_object_and_pydantic.ex01_type_annotations_and_coercion import (
    DataclassUserProfile,
    PydanticUserProfile,
    StrictPydanticUserProfile,
)
from data_object_and_pydantic.ex02_field_constraints_and_validation import (
    DataclassOrder,
    PydanticOrder,
)
from data_object_and_pydantic.ex03_json_serialization_and_schemas import (
    DataclassInvoice,
    PydanticInvoice,
    PaymentStatus,
)
from data_object_and_pydantic.ex05_domain_services_and_arbitrary_objects import (
    DataclassUserRepository,
    RawDatabaseConnection,
)


# ============================================================================
# 1. TYPE ANNOTATIONS & COERCION TESTS
# ============================================================================

def test_dataclass_allows_type_mismatch_without_error():
    """Verify dataclasses accept invalid runtime types without coercion or raising errors."""
    dc = DataclassUserProfile(
        user_id="999",  # String instead of int
        username="test_user",
        is_active="true",  # String instead of bool
        birth_date="2020-01-01",  # String instead of date object
        tags="invalid_tags"
    )
    # Dataclasses do not coerce! Values remain as passed strings.
    assert dc.user_id == "999"
    assert isinstance(dc.user_id, str)
    assert isinstance(dc.birth_date, str)


def test_pydantic_coerces_valid_string_inputs():
    """Verify Pydantic lax mode coerces compatible string inputs to target types."""
    py_model = PydanticUserProfile(
        user_id="999",
        username="test_user",
        is_active="true",
        birth_date="2020-01-01",
        tags=["dev"]
    )
    assert py_model.user_id == 999
    assert isinstance(py_model.user_id, int)
    assert py_model.is_active is True
    assert py_model.birth_date == date(2020, 1, 1)


def test_pydantic_strict_mode_rejects_coercion():
    """Verify Pydantic strict mode raises ValidationError when types do not match exactly."""
    with pytest.raises(ValidationError) as exc_info:
        StrictPydanticUserProfile(
            user_id="999",  # String rejected in strict mode
            username="test_user",
            is_active=True,
            birth_date=date(2020, 1, 1),
            tags=["dev"]
        )
    assert "user_id" in str(exc_info.value)


# ============================================================================
# 2. FIELD CONSTRAINTS & MUTATION VALIDATION TESTS
# ============================================================================

def test_dataclass_post_init_validation():
    """Verify Dataclass manual __post_init__ handles invalid arguments."""
    with pytest.raises(ValueError, match="quantity must be > 0"):
        DataclassOrder(order_id="ORD-1", quantity=-5, unit_price=10.0)


def test_pydantic_field_constraints_and_assignment_validation():
    """Verify Pydantic declarative field constraints and validate_assignment on mutation."""
    # Instantiation constraint failure
    with pytest.raises(ValidationError) as exc_info:
        PydanticOrder(order_id="ORD-101", quantity=0, unit_price=10.0)
    assert "quantity" in str(exc_info.value)

    # Valid instance
    order = PydanticOrder(order_id="ORD-101", quantity=5, unit_price=10.0, discount=0.1)
    assert order.total_price == 45.0

    # Mutation re-validation failure
    with pytest.raises(ValidationError):
        order.quantity = -10
    # Original value preserved
    assert order.quantity == 5


# ============================================================================
# 3. SERIALIZATION & SCHEMA TESTS
# ============================================================================

def test_pydantic_json_schema_generation():
    """Verify Pydantic model generates valid OpenAPI / JSON schema."""
    schema = PydanticInvoice.model_json_schema()
    assert schema["title"] == "PydanticInvoice"
    assert "invoiceId" in schema["properties"]
    assert "createdAt" in schema["properties"]


# ============================================================================
# 4. DOMAIN ENTITY & ARBITRARY OBJECT TESTS
# ============================================================================

def test_dataclass_handles_arbitrary_unserializable_objects():
    """Verify Dataclass seamlessly holds arbitrary stateful objects like database handles."""
    conn = RawDatabaseConnection("sqlite://test")
    repo = DataclassUserRepository(connection=conn)
    
    res = repo.fetch_user_by_id(1)
    assert res["id"] == 1
    assert repo._active_queries == 1
