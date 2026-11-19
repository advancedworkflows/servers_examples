"""
03_json_serialization_and_schemas.py

Demonstrates:
1. JSON Serialization & Deserialization of dataclasses vs Pydantic models.
2. Complex types (datetime, UUID, Decimal, Enum) handling in standard library vs Pydantic.
3. Field Aliasing (camelCase API contract vs snake_case Python code).
4. Automated JSON Schema generation (model_json_schema).

Target Audience: Mid/Senior Devs & Architects
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4
from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_serializer, AliasGenerator


# Common domain Enum
class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============================================================================
# 1. STANDARD DATACLASS SERIALIZATION DEMO
# ============================================================================

@dataclass
class DataclassInvoiceItem:
    description: str
    amount: Decimal


@dataclass
class DataclassInvoice:
    invoice_id: UUID
    created_at: datetime
    status: PaymentStatus
    items: List[DataclassInvoiceItem]


# Custom json.dumps encoder required for Dataclass!
class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def demonstrate_dataclass_serialization():
    print("\n" + "=" * 80)
    print("1. DATACLASS SERIALIZATION & MANUAL JSON ENCODING")
    print("=" * 80)

    invoice = DataclassInvoice(
        invoice_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        status=PaymentStatus.COMPLETED,
        items=[
            DataclassInvoiceItem(description="Cloud Server", amount=Decimal("150.75")),
            DataclassInvoiceItem(description="Domain Name", amount=Decimal("12.50"))
        ]
    )

    # 1. dataclasses.asdict() produces a standard Python dict
    raw_dict = asdict(invoice)
    print(f"[Dataclass asdict() Output]: {raw_dict}")
    print(f"  - invoice_id type in dict: {type(raw_dict['invoice_id']).__name__}")
    print(f"  - item amount type in dict: {type(raw_dict['items'][0]['amount']).__name__}")

    # 2. Attempting standard json.dumps(asdict(invoice)) FAILS natively:
    print("\nAttempting standard json.dumps(asdict(invoice)):")
    try:
        json.dumps(raw_dict)
    except TypeError as err:
        # 🐛 DEBUGPOINT 1: Place a breakpoint here!
        # Inspect 'err' to see that json.dumps cannot handle UUID, Decimal, datetime without custom encoders!
        print(f"  ❌ standard json.dumps failed: {err}")

    # 3. Successful JSON dumping requires custom encoder boilerplate:
    json_output = json.dumps(raw_dict, cls=DataclassJSONEncoder, indent=2)
    print(f"\n[Dataclass JSON with Custom Encoder]:\n{json_output}")


# ============================================================================
# 2. PYDANTIC MODEL SERIALIZATION & ALIASES DEMO
# ============================================================================

# Helper to convert snake_case -> camelCase for external API contracts
def to_camel(string: str) -> str:
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class PydanticInvoiceItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    description: str
    amount: Decimal


class PydanticInvoice(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,  # Allows instantiating via snake_case OR camelCase
        json_encoders={Decimal: lambda v: float(v)}  # Custom format override if needed
    )

    invoice_id: UUID
    created_at: datetime
    status: PaymentStatus
    items: List[PydanticInvoiceItem]

    # Custom Field Serializer example: format date as custom string during export
    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info: Any) -> str:
        # 🐛 DEBUGPOINT 2: Place a breakpoint inside this field_serializer!
        # Inspect 'dt' value and format it as ISO string or timestamp.
        return dt.isoformat()


def demonstrate_pydantic_serialization():
    print("\n" + "=" * 80)
    print("2. PYDANTIC SERIALIZATION, ALIASES & JSON SCHEMA GENERATION")
    print("=" * 80)

    p_invoice = PydanticInvoice(
        invoice_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        status=PaymentStatus.COMPLETED,
        items=[
            PydanticInvoiceItem(description="Cloud Server", amount=Decimal("150.75")),
            PydanticInvoiceItem(description="Domain Name", amount=Decimal("12.50"))
        ]
    )

    # 1. model_dump() (Python dictionary output)
    dict_snake = p_invoice.model_dump()
    print(f"[Pydantic model_dump() snake_case]: {dict_snake}")

    # 2. model_dump(by_alias=True) (API camelCase JSON dict)
    dict_camel = p_invoice.model_dump(by_alias=True)
    print(f"\n[Pydantic model_dump(by_alias=True) camelCase]: {dict_camel}")

    # 3. Native model_dump_json() (Direct ISO-compliant JSON string without extra encoders!)
    # 🐛 DEBUGPOINT 3: Place a breakpoint here!
    # Inspect 'json_str' output. Notice how UUID, datetime, Enum, and Decimal are seamlessly formatted.
    json_str = p_invoice.model_dump_json(by_alias=True, indent=2)
    print(f"\n[Pydantic model_dump_json(by_alias=True)]:\n{json_str}")

    # 4. JSON Schema Generation out-of-the-box
    print("\n" + "-" * 60)
    print("AUTOMATED JSON SCHEMA GENERATION (Draft 2020-12 / OpenAPI 3.1)")
    print("-" * 60)
    schema = PydanticInvoice.model_json_schema()
    # Print excerpt of generated schema
    print(f"Schema Title: {schema.get('title')}")
    print(f"Required Fields: {schema.get('required')}")
    print("Properties Excerpt:")
    for field_name, prop in schema.get("properties", {}).items():
        print(f"  - {field_name}: type={prop.get('type', prop.get('$ref', 'complex'))}")


if __name__ == "__main__":
    demonstrate_dataclass_serialization()
    demonstrate_pydantic_serialization()
