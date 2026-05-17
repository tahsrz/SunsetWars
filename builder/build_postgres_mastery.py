import sys
import os
from swarm_builder import SwarmMemoriaBuilder

def build_postgres_mastery():
    builder = SwarmMemoriaBuilder()
    
    # --- PERFORMANCE TUNING SECTOR ---
    
    # 1. Zero-Latency Profiling & Connection Management
    perf_text = (
        "PostgreSQL Performance: Use EXPLAIN (ANALYZE, BUFFERS) for query profiling. "
        "In serverless (Next.js), always use Supavisor (Transaction mode) to prevent connection exhaustion. "
        "Indexing: Use Covering Indexes (INCLUDE) for Index-Only scans. "
        "Anti-Patterns: Avoid 'SELECT *' and 'COUNT(*)' on large tables; use caching for counts."
    )
    perf_off = builder.add_swarm_shard(perf_text)
    builder.register_symbol("PG_PERF_TUNING", perf_off)
    
    # --- SECURITY & RLS SECTOR ---
    
    # 2. RLS Hardening & Data Isolation
    rls_text = (
        "Row Level Security (RLS): Policies are implicit WHERE clauses; columns in USING/CHECK must be indexed. "
        "Optimization: Wrap auth.uid() in a sub-select to force it as a constant for the planner. "
        "Security Definer: Always set a search_path for DEFINER functions to prevent hijacking. "
        "Mandatory for Sunset Pulse: Ensure 'leads' table uses { onConflict: 'email' } to respect unique constraints."
    )
    rls_off = builder.add_swarm_shard(rls_text, symbols=["PG_PERF_TUNING"])
    builder.register_symbol("RLS_HARDENING_PROTOCOL", rls_off)
    
    # --- JSONB SECTOR ---
    
    # 3. JSONB Indexing Strategies
    jsonb_text = (
        "JSONB Optimization: Use GIN (jsonb_path_ops) for containment (@>) queries—it is 20-30% smaller than default GIN. "
        "Functional Indexes: Create B-Tree indexes on specific high-frequency keys (e.g., metadata->>'status'). "
        "Storage: Use EXTERNAL storage for large blobs to keep table pages lean."
    )
    jsonb_off = builder.add_swarm_shard(jsonb_text, symbols=["PG_PERF_TUNING"])
    builder.register_symbol("JSONB_MASTERY", jsonb_off)

    # --- VECTOR SECTOR (AI) ---

    # 4. pg_vector & Semantic Search
    vector_text = (
        "pg_vector Ops: HNSW is the production standard for recall (<50M vectors) but has 2-5x memory overhead. "
        "IVFFlat is better for massive static datasets with limited memory. "
        "Distance Ops: Use vector_cosine_ops for OpenAI/Cohere. Pro-tip: Normalize vectors before insertion if using inner product."
    )
    vector_off = builder.add_swarm_shard(vector_text, symbols=["PG_PERF_TUNING"])
    builder.register_symbol("PG_VECTOR_SEMANTIC", vector_off)

    # 5. Hybrid Integration: Search + Security
    hybrid_text = (
        "Hybrid Postgres Pattern: Combining pg_vector semantic search with RLS for secure AI retrieval. "
        "Always enforce RLS on the embedding tables to ensure users only retrieve semantic matches they are authorized to see. "
        "Use Supabase 'rpc' calls to handle complex vector math inside Security Definer functions for performance."
    )
    hybrid_off = builder.add_swarm_shard(hybrid_text, symbols=["RLS_HARDENING_PROTOCOL", "PG_VECTOR_SEMANTIC"])
    builder.register_symbol("POSTGRES_HYBRID_PATTERNS", hybrid_off)

    # Save the cartridge
    builder.save_prototype("cartridges/postgres_mastery")
    print("Postgres Mastery Cartridge Compiled (v3.5 Swarm Protocol).")

if __name__ == "__main__":
    # Ensure builder is in path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    build_postgres_mastery()
