"""
05_domain_services_and_arbitrary_objects.py

Demonstrates:
1. Dataclasses as pure domain entities, rich object graphs, and stateful service objects.
2. Handling arbitrary non-serializable objects (DB pools, threading Locks, logger instances, custom SDK clients).
3. Friction when forcing Pydantic to manage arbitrary stateful service objects (arbitrary_types_allowed).

Target Audience: Mid/Senior Devs & Architects
"""

import sqlite3
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, PydanticSchemaGenerationError


# Dummy external service handle / un-serializable object
class RawDatabaseConnection:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._raw_conn = sqlite3.connect(":memory:")
        self._lock = threading.Lock()

    def execute_query(self, query: str) -> str:
        with self._lock:
            return f"Executed '{query}' on {self.db_url}"


# ============================================================================
# 1. STANDARD DATACLASS: NATURAL FIT FOR DOMAIN SERVICES & ARBITRARY STATE
# ============================================================================

@dataclass
class DataclassUserRepository:
    """
    Stateful Domain Repository service holding database connections and locks.
    Zero external dependencies, zero Pydantic validation overhead.
    """
    connection: RawDatabaseConnection
    cache_ttl_seconds: int = 300
    _active_queries: int = field(default=0, init=False)  # Internal mutable state

    def fetch_user_by_id(self, user_id: int) -> Dict[str, Any]:
        # 🐛 DEBUGPOINT 1: Place a breakpoint here!
        # Inspect self.connection (RawDatabaseConnection) and self._active_queries state.
        self._active_queries += 1
        res = self.connection.execute_query(f"SELECT * FROM users WHERE id = {user_id}")
        return {"id": user_id, "name": "Alice Domain", "db_result": res}


def demonstrate_dataclass_domain_service():
    print("\n" + "=" * 80)
    print("1. DATACLASS DOMAIN SERVICE & ARBITRARY OBJECT WIRING")
    print("=" * 80)

    db_conn = RawDatabaseConnection("sqlite://mem_db")
    repo = DataclassUserRepository(connection=db_conn, cache_ttl_seconds=600)

    print(f"[Dataclass Domain Service Instantiation]: {repo}")
    user_data = repo.fetch_user_by_id(42)
    print(f"  Service Execution Output: {user_data}")
    print(f"  Internal State (_active_queries): {repo._active_queries}")


# ============================================================================
# 2. PYDANTIC MODEL: FRICTION WITH ARBITRARY STATEFUL OBJECTS
# ============================================================================

# Attempt 1: Pydantic without arbitrary_types_allowed (FAILS AT SCHEMA GENERATION)
def demonstrate_pydantic_arbitrary_failure():
    print("\n" + "=" * 80)
    print("2. PYDANTIC DEFAULT BEHAVIOR WITH ARBITRARY OBJECTS (SCHEMA FAILURE)")
    print("=" * 80)

    try:
        class PydanticUserRepositoryDefault(BaseModel):
            connection: RawDatabaseConnection  # ⚠️ Raw un-serializable non-Pydantic type
            cache_ttl_seconds: int = 300

    except PydanticSchemaGenerationError as err:
        # 🐛 DEBUGPOINT 2: Place a breakpoint inside this except block!
        # Inspect 'err'. Pydantic cannot generate a schema for RawDatabaseConnection!
        print(f"  ❌ Pydantic Schema Generation Failed as expected:\n     {err}")


# Attempt 2: Pydantic WITH arbitrary_types_allowed=True (WORKAROUND WITH CAVEATS)
class PydanticUserRepositoryWorkaround(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)  # Workaround switch

    connection: RawDatabaseConnection
    cache_ttl_seconds: int = 300


def demonstrate_pydantic_arbitrary_workaround():
    print("\n" + "=" * 80)
    print("3. PYDANTIC WITH arbitrary_types_allowed=True (CAVEATS & OVERHEAD)")
    print("=" * 80)

    db_conn = RawDatabaseConnection("sqlite://pydantic_mem_db")
    p_repo = PydanticUserRepositoryWorkaround(connection=db_conn, cache_ttl_seconds=600)

    print(f"[Pydantic Service Workaround Instance]: {p_repo}")
    
    # CAVEAT 1: Serialization breaks!
    print("\nAttempting to call model_dump() on service holding arbitrary connection:")
    try:
        p_repo.model_dump()
    except Exception as err:
        print(f"  ⚠️ model_dump() warning/error on arbitrary type: {err}")

    # CAVEAT 2: Pydantic validation checks overhead on every initialization
    # for service wiring where validation is irrelevant.
    print("  Conclusion: Stateful services and domain logic belong in standard Dataclasses!")


if __name__ == "__main__":
    demonstrate_dataclass_domain_service()
    demonstrate_pydantic_arbitrary_failure()
    demonstrate_pydantic_arbitrary_workaround()
