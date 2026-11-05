"""
02_field_constraints_and_validation.py

Demonstrates:
1. Field constraints in standard dataclasses using __post_init__ vs Pydantic Field specs.
2. Custom field validation & cross-field validation rules (@field_validator vs @model_validator vs __post_init__).
3. Attribute mutation re-validation (validate_assignment).

Target Audience: Mid/Senior Devs & Architects
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ConfigDict


# ============================================================================
# 1. STANDARD DATACLASS: MANUAL VALIDATION VIA __post_init__
# ============================================================================

@dataclass
class DataclassOrder:
    order_id: str
    quantity: int
    unit_price: float
    discount: float = 0.0
    items: List[str] = field(default_factory=list)  # Mutable default MUST use default_factory!
    total_price: float = field(init=False)         # Calculated field, excluded from __init__

    def __post_init__(self):
        """
        __post_init__ runs AFTER __init__ completes.
        Manual validation logic and calculated field logic must be imperatively coded here.
        """
        # 🐛 DEBUGPOINT 1: Place a breakpoint here!
        # Inspect self.quantity, self.unit_price, self.discount before validation checks execute.
        if self.quantity <= 0:
            raise ValueError(f"quantity must be > 0, got {self.quantity}")
        if self.unit_price < 0:
            raise ValueError(f"unit_price must be >= 0, got {self.unit_price}")
        if not (0.0 <= self.discount <= 1.0):
            raise ValueError(f"discount must be between 0.0 and 1.0, got {self.discount}")

        # Compute calculated property
        self.total_price = round(self.quantity * self.unit_price * (1.0 - self.discount), 2)


def demonstrate_dataclass_constraints():
    print("\n" + "=" * 80)
    print("1. DATACLASS CONSTRAINTS & MANUAL VALIDATION (__post_init__)")
    print("=" * 80)

    # Valid Order
    order = DataclassOrder(order_id="ORD-101", quantity=5, unit_price=20.0, discount=0.1)
    print(f"[Dataclass Valid Order]: {order}")
    print(f"  Calculated total_price: ${order.total_price}")

    # Invalid Quantity (caught in __post_init__)
    try:
        DataclassOrder(order_id="ORD-102", quantity=-3, unit_price=15.0)
    except ValueError as e:
        print(f"  ❌ Caught manual __post_init__ error: {e}")

    # ⚠️ PITFALL OF DATACLASS MUTATION:
    # __post_init__ ONLY runs once during instantiation (__init__).
    # Mutating attributes directly afterwards BYPASSES validation silently!
    order.quantity = -999  # Validation is NOT re-triggered!
    print(f"  ⚠️ After Direct Mutation: order.quantity={order.quantity} (Validation was bypassed!)")


# ============================================================================
# 2. PYDANTIC MODEL: DECLARATIVE FIELD CONSTRAINTS & VALIDATORS
# ============================================================================

class PydanticOrder(BaseModel):
    # Enforce attribute re-validation whenever an attribute is modified
    model_config = ConfigDict(validate_assignment=True)

    # Declarative constraints directly in Field(...) definition
    order_id: str = Field(..., pattern=r"^ORD-\d+$", description="Order format: ORD-<number>")
    quantity: int = Field(..., gt=0, le=1000, description="Quantity between 1 and 1000")
    unit_price: float = Field(..., ge=0.0, description="Unit price cannot be negative")
    discount: float = Field(default=0.0, ge=0.0, le=1.0, description="Discount factor [0.0 - 1.0]")
    items: List[str] = Field(default_factory=list)

    # Calculated / computed field
    @property
    def total_price(self) -> float:
        return round(self.quantity * self.unit_price * (1.0 - self.discount), 2)

    # Custom Field Validator (runs on order_id or custom field logic)
    @field_validator("order_id", mode="after")
    @classmethod
    def validate_order_id_prefix(cls, value: str) -> str:
        # 🐛 DEBUGPOINT 2: Place a breakpoint inside this field_validator!
        # Inspect 'value' parameter before returning upper-cased/validated value.
        if not value.startswith("ORD-"):
            raise ValueError("order_id must start with prefix 'ORD-'")
        return value.upper()

    # Cross-Field Model Validator (evaluates whole model state after individual fields pass)
    @model_validator(mode="after")
    def validate_discount_for_bulk_orders(self) -> "PydanticOrder":
        # 🐛 DEBUGPOINT 3: Place a breakpoint inside this model_validator!
        # Inspect self.quantity and self.discount to check cross-field business logic.
        if self.quantity < 5 and self.discount > 0.2:
            raise ValueError("Discounts over 20% require a minimum quantity of 5 items!")
        return self


def demonstrate_pydantic_constraints():
    print("\n" + "=" * 80)
    print("2. PYDANTIC CONSTRAINTS, FIELD VALIDATORS & MUTATION RE-VALIDATION")
    print("=" * 80)

    # Valid Order
    p_order = PydanticOrder(order_id="ORD-555", quantity=10, unit_price=15.50, discount=0.25)
    print(f"[Pydantic Valid Order]: {p_order!r}")
    print(f"  Calculated total_price property: ${p_order.total_price}")

    # Field Constraint Error (quantity out of bounds)
    print("\nAttempting quantity <= 0:")
    try:
        PydanticOrder(order_id="ORD-101", quantity=0, unit_price=10.0)
    except ValidationError as e:
        print(f"  ❌ Caught Pydantic Field constraint error: {e.errors()[0]['msg']}")

    # Cross-field business rule error (high discount with low quantity)
    print("\nAttempting high discount on low quantity (cross-field validator):")
    try:
        PydanticOrder(order_id="ORD-102", quantity=2, unit_price=10.0, discount=0.30)
    except ValidationError as e:
        print(f"  ❌ Caught Pydantic Cross-Field error: {e.errors()[0]['msg']}")

    # 🛡️ MUTATION RE-VALIDATION (validate_assignment=True):
    print("\nAttempting attribute mutation on valid instance:")
    try:
        p_order.quantity = -50  # Triggers validation instantly on assignment!
    except ValidationError as e:
        # 🐛 DEBUGPOINT 4: Place a breakpoint here!
        # Notice how validate_assignment=True intercepted the invalid assignment!
        print(f"  🛡️ Mutation blocked by validate_assignment=True: {e.errors()[0]['msg']}")
        print(f"  Current value preserved safely: p_order.quantity={p_order.quantity}")


if __name__ == "__main__":
    demonstrate_dataclass_constraints()
    demonstrate_pydantic_constraints()
