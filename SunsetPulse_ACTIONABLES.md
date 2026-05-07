# SunsetPulse Tactical Actionables: TAH & SICP Principles

Apply these high-performance, edge-based architectural patterns to the SunsetPulse (IDX/Real Estate) engine.

---

## 1. The Listing Gate (Probabilistic Filtering)
**Concept**: Use the TAH Bloom Filter logic to validate property listing updates before they hit the database.
-   **Problem**: Ingesting 100k+ listings from NTREIS/MLS is database-intensive. Most listings haven't changed.
-   **Action**: Create a `listings_bloom.tah` cartridge. When an update arrives, check the filter first. If "Not Present," it's a new listing—UPSERT. If "Possibly Present," only then check the hash/timestamp in the DB.
-   **Benefit**: Reduces DB read IOPS by ~80%.

## 2. Asynchronous Ingestion Streams (The Pulse)
**Concept**: Treat the NTREIS MLS feed as an infinite **SICP Stream**.
-   **Problem**: Standard iteration over listing arrays causes memory spikes and stalls during network latency.
-   **Action**: Implement `ListingStream` using the `PulseStream` pattern. Use lazy evaluation (`yield`) to process properties as they arrive.
-   **Benefit**: Decouples "Listing Fetching" from "Data Normalization," allowing the system to handle 100k records on low-memory edge workers.

## 3. Programmable Search (Metacircular Evaluator)
**Concept**: Move beyond static SQL filters to a **Lisp-style Property Evaluator**.
-   **Problem**: Complex real estate queries (e.g., "3 beds in Dallas under $500k near a park") result in massive, slow SQL `WHERE` clauses.
-   **Action**: Implement a `SearchEvaluator`. Convert user queries into S-Expressions: `(SEARCH "dallas" :price-max 500k :beds-min 3 :near "Lakeside Park")`.
-   **Benefit**: Allows for "Programmable Alerts" and highly complex user-defined retrieval logic without SQL injection risks.

## 4. Neighborhood Intelligence Cartridges (Spatial Linking)
**Concept**: Forge `.tah` cartridges for local metadata (Schools, Transit, Crime Stats).
-   **Problem**: Joining property tables with massive spatial datasets (neighborhood boundaries) is slow.
-   **Action**: Forge a `neighborhoods_dallas.tah` using the **Coordinate Shard (Type 1)**. Link properties to these shards using **Binary Linking**.
-   **Benefit**: The terminal can show "Schools nearby" instantly using an O(1) binary seek rather than a heavy PostGIS join.

---

### 🧪 Immediate Prototype: The Listing Gate
```python
from builder.tah_builder import TAHBuilder

def forge_listing_gate(mls_ids):
    # expected_elements should be 2x total listings
    gate = TAHBuilder(target_fp=0.0001, expected_elements=200000)
    for mls_id in mls_ids:
        gate._add_to_global_filter(str(mls_id))
    gate.save("cartridges/listings_gate.tah")
```

---
*Actionable Next Step: Shall we implement the `ListingStream` in the SunsetPulse ingestor?*
