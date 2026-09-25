"""
06_performance_and_benchmarks.py

Demonstrates:
1. Micro-benchmarking instantiation speed: Dataclass vs Dataclass(slots=True) vs Pydantic vs model_construct().
2. Memory consumption footprint comparison using sys.getsizeof().
3. Pragmatic takeaways for architects: when runtime validation overhead matters vs when network I/O dominates.

Target Audience: Mid/Senior Devs & Architects
"""

import sys
import time
from dataclasses import dataclass
from typing import List
from pydantic import BaseModel, ConfigDict


# Test models representing a typical DTO / Domain record with 4 fields
@dataclass
class StandardDataclassPoint:
    x: float
    y: float
    label: str
    is_active: bool


@dataclass(slots=True)
class SlottedDataclassPoint:
    x: float
    y: float
    label: str
    is_active: bool


class PydanticPoint(BaseModel):
    x: float
    y: float
    label: str
    is_active: bool


ITERATIONS = 200_000


def run_instantiation_benchmarks():
    print("\n" + "=" * 80)
    print(f"PERFORMANCE BENCHMARK: INSTANTIATING {ITERATIONS:,} OBJECTS")
    print("=" * 80)

    # 1. Standard Dataclass
    start_time = time.perf_counter()
    for i in range(ITERATIONS):
        _ = StandardDataclassPoint(x=12.5, y=42.3, label="sensor_1", is_active=True)
    dc_time = time.perf_counter() - start_time
    print(f"1. Standard Dataclass:            {dc_time:.4f}s ({ITERATIONS/dc_time:,.0f} ops/sec)")

    # 2. Slotted Dataclass
    start_time = time.perf_counter()
    for i in range(ITERATIONS):
        _ = SlottedDataclassPoint(x=12.5, y=42.3, label="sensor_1", is_active=True)
    dc_slots_time = time.perf_counter() - start_time
    print(f"2. Dataclass (slots=True):        {dc_slots_time:.4f}s ({ITERATIONS/dc_slots_time:,.0f} ops/sec)")

    # 3. Pydantic BaseModel (Full Runtime Validation)
    start_time = time.perf_counter()
    for i in range(ITERATIONS):
        _ = PydanticPoint(x=12.5, y=42.3, label="sensor_1", is_active=True)
    py_time = time.perf_counter() - start_time
    print(f"3. Pydantic BaseModel (validated): {py_time:.4f}s ({ITERATIONS/py_time:,.0f} ops/sec)")

    # 4. Pydantic BaseModel (model_construct - validation bypassed)
    start_time = time.perf_counter()
    for i in range(ITERATIONS):
        _ = PydanticPoint.model_construct(x=12.5, y=42.3, label="sensor_1", is_active=True)
    py_construct_time = time.perf_counter() - start_time
    print(f"4. Pydantic (model_construct):     {py_construct_time:.4f}s ({ITERATIONS/py_construct_time:,.0f} ops/sec)")

    # Speed ratio analysis
    ratio = py_time / dc_time
    print(f"\n  📊 Standard Dataclass is approx {ratio:.1f}x FASTER at instantiation than validated Pydantic!")
    print("     (Pydantic V2 is fast C/Rust code, but runtime validation overhead is real).")


def run_memory_footprint_analysis():
    print("\n" + "=" * 80)
    print("MEMORY FOOTPRINT ANALYSIS (sys.getsizeof)")
    print("=" * 80)

    dc_inst = StandardDataclassPoint(x=12.5, y=42.3, label="sensor_1", is_active=True)
    dc_slots_inst = SlottedDataclassPoint(x=12.5, y=42.3, label="sensor_1", is_active=True)
    py_inst = PydanticPoint(x=12.5, y=42.3, label="sensor_1", is_active=True)

    dc_size = sys.getsizeof(dc_inst) + sys.getsizeof(dc_inst.__dict__)
    dc_slots_size = sys.getsizeof(dc_slots_inst)
    py_size = sys.getsizeof(py_inst) + sys.getsizeof(py_inst.__dict__)

    # 🐛 DEBUGPOINT 1: Place a breakpoint here!
    # Inspect 'dc_size', 'dc_slots_size', 'py_size' in debugger.
    print(f"1. Standard Dataclass Instance + __dict__: {dc_size} bytes")
    print(f"2. Slotted Dataclass Instance (slots=True): {dc_slots_size} bytes")
    print(f"3. Pydantic Instance + __dict__:           {py_size} bytes")

    print("\n" + "-" * 60)
    print("ARCHITECTURAL IMPLICATIONS FOR HIGH-THROUGHPUT PIPELINES")
    print("-" * 60)
    print("""
    💡 ARCHITECTURAL DECISION RULE:
    1. NETWORK BOUNDARY (FastAPI HTTP requests / JSON API / Message Queues):
       -> Use PYDANTIC. Validation cost (~microseconds) is trivial compared to network I/O (~milliseconds).
    2. INTERNAL DOMAIN LOGIC / IN-MEMORY PROCESSING (100k+ DB records in loop):
       -> Use DATACLASS (with slots=True). Avoid validation overhead on internal trusted data structures.
    """)


if __name__ == "__main__":
    run_instantiation_benchmarks()
    run_memory_footprint_analysis()
