"""
app.py - Production-Grade FastAPI Application Architecture

Demonstrates proper architectural separation of concerns:
1. Pydantic at the Trust Boundary (API Controller / Transport Layer).
2. Dataclasses in the Core Domain Layer (Internal Entities & Service Wiring).
3. Explicit Mapping Layer between Transport DTOs and Domain Entities.

Target Audience: Mid/Senior Devs & Architects
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict


app = FastAPI(
    title="Dataclass vs Pydantic Architecture Blueprint",
    version="1.0.0",
    description="Demonstrates clean separation: Pydantic for API Trust Boundaries, Dataclasses for Core Domain Entities."
)


# ============================================================================
# 1. CORE DOMAIN LAYER (INTERNAL REALM - STDLIB DATACLASSES)
# ============================================================================

@dataclass(slots=True)
class CustomerDomainEntity:
    customer_id: UUID
    name: str
    email: str


@dataclass(slots=True)
class OrderItemDomainEntity:
    product_code: str
    quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price


@dataclass
class OrderDomainEntity:
    """
    Internal Domain Entity representing an Order.
    Calculates business metrics and manages internal domain state.
    """
    order_id: UUID
    customer: CustomerDomainEntity
    items: List[OrderItemDomainEntity]
    status: str = "CREATED"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_amount(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0.00"))


@dataclass
class OrderDomainService:
    """
    Core Domain Service for order fulfillment.
    Stateful service object wired using Dataclass.
    """
    service_name: str = "CoreFulfillmentService"

    def process_order(self, order: OrderDomainEntity) -> OrderDomainEntity:
        # 🐛 DEBUGPOINT 1: Place a breakpoint inside process_order!
        # Inspect order (OrderDomainEntity), customer details, and total_amount calculation.
        if not order.items:
            raise ValueError("Cannot process an empty order!")
        
        # Apply domain business rule: update status
        order.status = "PROCESSED"
        return order


# Global Service Singleton
fulfillment_service = OrderDomainService()


# ============================================================================
# 2. TRANSPORT / API LAYER (TRUST BOUNDARY - PYDANTIC V2)
# ============================================================================

# Request DTO (Pydantic validation at network boundary)
class OrderItemDTO(BaseModel):
    product_code: str = Field(..., pattern=r"^[A-Z]{3}-\d{3}$", description="Format: PRD-123")
    quantity: int = Field(..., gt=0, le=100)
    unit_price: float = Field(..., gt=0.0)


class CustomerDTO(BaseModel):
    customer_id: UUID
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")


class CreateOrderRequestDTO(BaseModel):
    customer: CustomerDTO
    items: List[OrderItemDTO] = Field(..., min_length=1)


# Response DTO (Pydantic contract definition for frontend/clients)
class OrderResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    status: str
    total_amount: float
    item_count: int
    processed_at: datetime


# Direct Dataclass Endpoint Model
@dataclass
class DirectDataclassPayload:
    title: str
    priority: int = 1


# ============================================================================
# 3. FASTAPI CONTROLLER / ENDPOINTS
# ============================================================================

@app.post(
    "/api/v1/orders",
    response_model=OrderResponseDTO,
    status_code=status.HTTP_201_CREATED,
    tags=["API Trust Boundary (Pydantic DTOs)"]
)
def create_order(request_dto: CreateOrderRequestDTO):
    """
    Clean Architecture Endpoint:
    1. Receives and validates incoming request payload via Pydantic (Request DTO).
    2. Maps Pydantic DTO -> Dataclass Domain Entity.
    3. Invokes Core Domain Service.
    4. Maps Dataclass Domain Entity -> Pydantic Response DTO.
    """
    # 🐛 DEBUGPOINT 2: Place a breakpoint here!
    # Inspect request_dto (validated Pydantic model) before domain mapping.

    # 1. Map Pydantic DTO -> Dataclass Domain Entities
    domain_customer = CustomerDomainEntity(
        customer_id=request_dto.customer.customer_id,
        name=request_dto.customer.name,
        email=request_dto.customer.email
    )

    domain_items = [
        OrderItemDomainEntity(
            product_code=item.product_code,
            quantity=item.quantity,
            unit_price=Decimal(str(item.unit_price))
        )
        for item in request_dto.items
    ]

    domain_order = OrderDomainEntity(
        order_id=uuid4(),
        customer=domain_customer,
        items=domain_items
    )

    # 2. Execute Core Domain Logic
    try:
        processed_order = fulfillment_service.process_order(domain_order)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    # 3. Map Dataclass Domain Entity -> Pydantic Response DTO
    return OrderResponseDTO(
        order_id=processed_order.order_id,
        status=processed_order.status,
        total_amount=float(processed_order.total_amount),
        item_count=len(processed_order.items),
        processed_at=processed_order.created_at
    )


@app.post(
    "/api/v1/direct-dataclass",
    tags=["Direct Dataclass Handling"]
)
def handle_direct_dataclass(payload: DirectDataclassPayload):
    """
    Endpoint accepting standard @dataclass directly.
    Demonstrates FastAPI's internal wrapper for stdlib dataclasses.
    """
    # 🐛 DEBUGPOINT 3: Place a breakpoint here!
    # Inspect type(payload) -> <class 'DirectDataclassPayload'>
    return {
        "message": "Direct dataclass handled successfully",
        "title": payload.title,
        "priority": payload.priority
    }


@app.get(
    "/api/v1/comparison-schema",
    tags=["Schema Inspection"]
)
def compare_schemas():
    """
    Returns side-by-side JSON Schemas generated for Pydantic CreateOrderRequestDTO vs DirectDataclassPayload.
    """
    pydantic_schema = CreateOrderRequestDTO.model_json_schema()
    return {
        "pydantic_dto_schema": pydantic_schema,
        "dataclass_note": "FastAPI wraps DirectDataclassPayload with Pydantic internally at route definition time."
    }
