"""
01_type_annotations_and_coercion.py

Demonstrates:
1. Dataclass static-only type hint checking vs Pydantic runtime validation & coercion.
2. Default lax coercion in Pydantic vs Strict mode.
3. Catching and inspecting Pydantic validation errors vs Silent type mismatches in Dataclass.

Target Audience: Mid/Senior Devs & Architects
"""

from dataclasses import dataclass
from datetime import date
from typing import List
from pydantic import BaseModel, ConfigDict, Field, ValidationError


# ============================================================================
# 1. STANDARD DATACLASS DEMO
# ============================================================================

@dataclass
class DataclassUserProfile:
    user_id: int
    username: str
    is_active: bool
    birth_date: date
    tags: List[str]


def demonstrate_dataclass_behavior():
    print("\n" + "=" * 80)
    print("1. DATACLASS BEHAVIOR: STATIC TYPE HINTS ONLY (NO RUNTIME VALIDATION/COERCION)")
    print("=" * 80)

    # Valid instantiation
    valid_dc = DataclassUserProfile(
        user_id=101,
        username="alice_dev",
        is_active=True,
        birth_date=date(1990, 5, 15),
        tags=["admin", "developer"]
    )
    print(f"[Dataclass Valid] {valid_dc}")

    # INVALID INSTANTIATION AT RUNTIME:
    # Notice we pass:
    # - user_id as a string "999" (expected int)
    # - is_active as a string "yes" (expected bool)
    # - birth_date as string "1995-10-20" (expected datetime.date)
    # Dataclasses DO NOT coerce types or raise runtime errors!
    invalid_dc = DataclassUserProfile(
        user_id="999",         # ⚠️ Type mismatch: string instead of int
        username="bob_builder",
        is_active="yes",       # ⚠️ Type mismatch: string instead of bool
        birth_date="1995-10-20", # ⚠️ Type mismatch: string instead of date object
        tags="not-a-list"      # ⚠️ Type mismatch: string instead of list
    )

    # 🐛 DEBUGPOINT 1: Place a breakpoint on the line below!
    # Inspect 'invalid_dc.__dict__' in your debugger.
    # Notice: invalid_dc.user_id is STILL str ('999'), NOT int!
    # Dataclasses do zero checking or conversion at runtime.
    print(f"[Dataclass Invalid Instantiation Succeeded!]:")
    print(f"  - user_id: {invalid_dc.user_id!r} (type: {type(invalid_dc.user_id).__name__})")
    print(f"  - is_active: {invalid_dc.is_active!r} (type: {type(invalid_dc.is_active).__name__})")
    print(f"  - birth_date: {invalid_dc.birth_date!r} (type: {type(invalid_dc.birth_date).__name__})")
    
    # downstream operations can silently break later!
    try:
        # Expecting date object methods like .year will fail at runtime far from creation point!
        _ = invalid_dc.birth_date.year
    except AttributeError as err:
        print(f"  ⚠️ Runtime Error downstream when calling date method: {err}")


# ============================================================================
# 2. PYDANTIC LAX COERCION DEMO
# ============================================================================

class PydanticUserProfile(BaseModel):
    user_id: int
    username: str
    is_active: bool
    birth_date: date
    tags: List[str]


def demonstrate_pydantic_lax_behavior():
    print("\n" + "=" * 80)
    print("2. PYDANTIC LAX BEHAVIOR: RUNTIME VALIDATION & AUTOMATIC COERCION")
    print("=" * 80)

    # Passing raw string inputs that can be coerced:
    # - "999" -> converted to int 999
    # - "true" / "1" / "yes" -> converted to bool True
    # - "1995-10-20" -> converted to date(1995, 10, 20)
    # - ("admin", "dev") tuple -> converted to list ["admin", "dev"]
    pydantic_user = PydanticUserProfile(
        user_id="999",
        username="charlie",
        is_active="true",
        birth_date="1995-10-20",
        tags=("admin", "dev")
    )

    # 🐛 DEBUGPOINT 2: Place a breakpoint on the line below!
    # Inspect 'pydantic_user.user_id', 'pydantic_user.birth_date', 'pydantic_user.is_active'.
    # Notice: 'pydantic_user.user_id' is now int (999), and 'birth_date' is date object!
    print(f"[Pydantic Coerced Instance]: {pydantic_user!r}")
    print(f"  - user_id: {pydantic_user.user_id!r} (type: {type(pydantic_user.user_id).__name__})")
    print(f"  - is_active: {pydantic_user.is_active!r} (type: {type(pydantic_user.is_active).__name__})")
    print(f"  - birth_date: {pydantic_user.birth_date!r} (type: {type(pydantic_user.birth_date).__name__})")
    print(f"  - tags: {pydantic_user.tags!r} (type: {type(pydantic_user.tags).__name__})")

    # What happens when input CANNOT be coerced?
    print("\nAttempting invalid un-coercible input into Pydantic:")
    try:
        _ = PydanticUserProfile(
            user_id="not_an_int",
            username="invalid_user",
            is_active="maybe",
            birth_date="invalid-date-format",
            tags=12345
        )
    except ValidationError as e:
        # 🐛 DEBUGPOINT 3: Place a breakpoint inside this except block!
        # Inspect 'e.errors()' to see the detailed structured error list returned by Pydantic.
        print(f"  ❌ Validation Failed with {e.error_count()} error(s):")
        for err in e.errors():
            print(f"    -> Field '{'.'.join(str(loc) for loc in err['loc'])}': {err['msg']} (type={err['type']})")


# ============================================================================
# 3. PYDANTIC STRICT MODE DEMO
# ============================================================================

class StrictPydanticUserProfile(BaseModel):
    model_config = ConfigDict(strict=True)  # Enforce strict type matching globally for this model

    user_id: int
    username: str
    is_active: bool
    birth_date: date
    # Or enforce strict mode on a single field using Field(strict=True)
    tags: List[str] = Field(strict=True)


def demonstrate_pydantic_strict_behavior():
    print("\n" + "=" * 80)
    print("3. PYDANTIC STRICT MODE: NO COERCION ALLOWED")
    print("=" * 80)

    try:
        # In strict mode, string "999" will NOT be coerced to int 999!
        _ = StrictPydanticUserProfile(
            user_id="999",  # Fails in strict mode
            username="diana",
            is_active=True,
            birth_date=date(1998, 1, 1),
            tags=["lead"]
        )
    except ValidationError as e:
        # 🐛 DEBUGPOINT 4: Place a breakpoint here!
        # Inspect 'e.errors()' - strict mode requires exact types (int, not str).
        print("  ❌ Strict Mode Rejected string '999' for int field:")
        for err in e.errors():
            print(f"    -> Field '{'.'.join(str(loc) for loc in err['loc'])}': {err['msg']}")


if __name__ == "__main__":
    demonstrate_dataclass_behavior()
    demonstrate_pydantic_lax_behavior()
    demonstrate_pydantic_strict_behavior()
