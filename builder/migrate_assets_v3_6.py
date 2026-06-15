import sys
import os
import time

# Add current dir to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memoria_builder import MemoriaBuilder

def migrate_assets():
    """
    Knowledge Rescue Operation: Migrating all core assets to v3.6 Intelligence Protocol.
    Links legacy knowledge to the Global Grid (USA_TX, USA_CA, etc.)
    """
    builder = MemoriaBuilder(expected_elements=10000)
    
    print("🚀 Initiating Knowledge Asset Migration to v3.6...")

    # 1. SECURITY ARCHITECT (Identity/NIST/Crypto)
    print("📦 Migrating: Security Architect...")
    security_origin = "https://nist.gov/publications/sp-800-207"
    builder.add_text_shard(
        "Zero Trust Architecture (NIST SP 800-207): Identity is the new perimeter. Principles: Explicit Verification, Least Privilege, and Assume Breach. Access is granted per-session based on user/device/risk signals.",
        url=security_origin, location="USA_TX", relevance=0.98
    )
    builder.add_text_shard(
        "IAM Hardening: AWS SCPs and Azure PIM are critical for restricting high-risk actions. Use Managed Identities to eliminate static credentials. MFA is mandatory for all console/CLI access.",
        url="https://aws.amazon.com/iam/hardening", location="USA_CA", relevance=0.95
    )
    builder.add_text_shard(
        "ECC (Elliptic Curve Cryptography): 256-bit ECC matches 3072-bit RSA security with lower CPU. Core Primitives: ECDSA for signatures, ECDHE for key exchange, and Ed25519 for side-channel resistance.",
        url="https://en.wikipedia.org/wiki/Elliptic-curve_cryptography", location="UK", relevance=0.90
    )

    # 2. POSTGRES MASTERY (High Availability / GIS)
    print("📦 Migrating: Postgres Mastery...")
    pg_origin = "https://www.postgresql.org/docs/"
    builder.add_text_shard(
        "PostgreSQL WAL (Write-Ahead Logging): Ensures data integrity by logging changes before applying to data files. Critical for crash recovery and streaming replication (Primary -> Standby).",
        url=pg_origin, location="USA_NY", relevance=0.92
    )
    builder.add_text_shard(
        "PostGIS Spatial Indexing: Uses GIST (Generalized Search Tree) for high-performance geometric queries. Enables Sunset Pulse's O(1) property boundary lookups via R-Tree algorithms.",
        url="https://postgis.net/docs/", location="USA_FL", relevance=0.97
    )

    # 3. SPATIAL COMPUTING (Three.js / IDX)
    print("📦 Migrating: Spatial Computing...")
    builder.add_text_shard(
        "Three.js Scene Graph Optimization: Using Frustum Culling and InstancedMesh to render 10,000+ property boundaries at 60FPS. BVH (Bounding Volume Hierarchy) ensures sub-millisecond collision detection.",
        url="https://threejs.org/docs/", location="JP", relevance=0.94
    )
    builder.add_text_shard(
        "IDX/RETS Protocol Handshake: NTREIS uses XML/SOAP for initial metadata exchange. Modern implementations transition to Web API (OData/JSON) for sub-second property updates.",
        url="https://www.reso.org/web-api/", location="USA_TX", relevance=0.96
    )

    # 4. WEB FOUNDATIONS (Next.js / TypeScript)
    print("📦 Migrating: Web Foundations...")
    builder.add_text_shard(
        "Next.js Server Components (RSC): Zero-bundle-size React components that run exclusively on the server. Ideal for intelligence-heavy dashboards that fetch TAH cartridges directly from the filesystem.",
        url="https://nextjs.org/docs/app/building-your-application/rendering/server-components", location="USA_CA", relevance=0.93
    )

    # --- NEW INTELLIGENCE EXPANSION (8 ADDITIONAL SOURCES) ---

    # 5. MAPPING & VISUALS (Mapbox)
    print("📦 Expanding: Mapping Intelligence...")
    builder.add_text_shard(
        "Mapbox Vector Tiles (MVT): Highly efficient encoded geographic data that allows for dynamic styling and O(1) rendering of complex property boundaries in the browser.",
        url="https://docs.mapbox.com/vector-tiles/reference/", location="USA_CA", relevance=0.95
    )

    # 6. REAL-TIME DATA (Supabase)
    print("📦 Expanding: Real-Time Infrastructure...")
    builder.add_text_shard(
        "Supabase Realtime: Uses PostgreSQL Logical Replication via the WAL to broadcast database changes to clients over WebSockets. Critical for live lead-activity tracking in Sunset Pulse.",
        url="https://supabase.com/docs/guides/realtime", location="USA_TX", relevance=0.98
    )

    # 7. LLM ORCHESTRATION (OpenRouter)
    print("📦 Expanding: Intelligence Orchestration...")
    builder.add_text_shard(
        "OpenRouter API: A unified interface for accessing high-performance LLMs (Claude 3.5, Gemini 1.5). Implements dynamic routing and cost-optimization for high-stakes intelligence processing.",
        url="https://openrouter.ai/docs", location="JP", relevance=0.91
    )

    # 8. DATA STANDARDS (NTREIS / RESO)
    print("📦 Expanding: Real Estate Standards...")
    builder.add_text_shard(
        "RESO Data Dictionary: The common language for real estate data, ensuring interoperability between NTREIS, MLS systems, and the Sunset Pulse engine.",
        url="https://www.reso.org/data-dictionary/", location="USA_TX", relevance=0.97
    )

    # 9. DATA INTEGRITY (Zod)
    print("📦 Expanding: Schema Validation...")
    builder.add_text_shard(
        "Zod Type-Safety: A TypeScript-first schema validation library. Ensures that all binary data extracted from TAH shards matches expected runtime interfaces with zero-cost validation.",
        url="https://zod.dev/", location="DE", relevance=0.90
    )

    # 10. INFRASTRUCTURE (Docker)
    print("📦 Expanding: Containerization...")
    builder.add_text_shard(
        "Docker Multi-Stage Builds: Minimizes production image size by separating build-time dependencies from the runtime environment. Ensures rapid deployment of the Pulse engine across Azure/AWS.",
        url="https://docs.docker.com/build/building/multi-stage/", location="FR", relevance=0.88
    )

    # 11. HASHING PERFORMANCE (CityHash)
    print("📦 Expanding: Binary Performance...")
    builder.add_text_shard(
        "CityHash64: A high-performance non-cryptographic hash function optimized for string lookup. Powering the O(1) surgical matching in the Memoria v3.6 Protocol.",
        url="https://github.com/google/cityhash", location="UK", relevance=0.94
    )

    # 12. UI ARCHITECTURE (Tailwind CSS)
    print("📦 Expanding: Visual Architecture...")
    builder.add_text_shard(
        "Tailwind CSS Utility-First Design: A CSS framework for rapid UI development. Enables Sunset Pulse's 'Premium Tech' aesthetic through consistent spacing, gradients, and typography scales.",
        url="https://tailwindcss.com/docs/utility-first", location="USA_NY", relevance=0.92
    )

    # --- FINAL INTELLIGENCE SATURATION (8 ADDITIONAL SOURCES) ---

    # 13. LLM SPEED (Groq)
    print("📦 Saturating: LPU Inference Speed...")
    builder.add_text_shard(
        "Groq LPU (Language Processing Unit): Deterministic, ultra-low latency hardware for LLM inference. Powering the sub-second 'Jamie Pulse' responses for lead re-engagement scripts.",
        url="https://wow.groq.com/lpu-architecture-whitepaper/", location="USA_CA", relevance=0.99
    )

    # 14. 3D PHYSICS (Cannon.js / Three.js)
    print("📦 Saturating: Spatial Physics...")
    builder.add_text_shard(
        "Cannon.js Integration: A lightweight 3D physics engine. Enables realistic property boundary interaction and 3D collision detection for the Sunset Pulse spatial search interface.",
        url="https://pmndrs.github.io/cannon-es/", location="DE", relevance=0.89
    )

    # 15. AUTHENTICATION (JWT / JOSE)
    print("📦 Saturating: Secure Token Exchange...")
    builder.add_text_shard(
        "JWT (JSON Web Tokens): Uses the JOSE (JSON Object Signing and Encryption) suite for stateless authentication. Sunset Pulse UI uses ES256 (Elliptic Curve) signatures for maximum security.",
        url="https://jwt.io/introduction", location="UK", relevance=0.96
    )

    # 16. CI/CD AUTOMATION (GitHub Actions)
    print("📦 Saturating: Deployment Pipelines...")
    builder.add_text_shard(
        "GitHub Actions: Automated workflows for CI/CD. Sunset Pulse uses multi-job runners to build Docker images and deploy to Azure Web Apps on every push to 'main'.",
        url="https://github.com/features/actions", location="USA_TX", relevance=0.94
    )

    # 17. SEARCH OPTIMIZATION (BM25)
    print("📦 Saturating: Ranking Algorithms...")
    builder.add_text_shard(
        "BM25 (Best Matching 25): A ranking function used by search engines to estimate the relevance of shards to a given search query. Implemented in Python for the TAH v3.6 Query Engine.",
        url="https://en.wikipedia.org/wiki/Okapi_BM25", location="FR", relevance=0.91
    )

    # 18. DATA STREAMS (Redis)
    print("📦 Saturating: In-Memory Orchestration...")
    builder.add_text_shard(
        "Redis Pub/Sub: High-performance messaging for real-time data streams. Used as a buffer for incoming NTREIS property updates before they are committed to the Supabase WAL.",
        url="https://redis.io/docs/manual/pubsub/", location="USA_FL", relevance=0.93
    )

    # 19. REACTIVE STATE (Zustand)
    print("📦 Saturating: UI State Management...")
    builder.add_text_shard(
        "Zustand State Management: A small, fast, and scalable bearbones state-management solution. Manages the global 'Pulse Map' state without the overhead of heavy context providers.",
        url="https://docs.pmnd.rs/zustand/getting-started/introduction", location="USA_NY", relevance=0.90
    )

    # 20. ASYNC RUNTIME (Node.js)
    print("📦 Saturating: Serverless Infrastructure...")
    builder.add_text_shard(
        "Node.js Event Loop: Non-blocking I/O model that allows for handling thousands of concurrent TAH cartridge requests. The backbone of the Gemini-CLI-UI server.",
        url="https://nodejs.org/en/about", location="JP", relevance=0.95
    )

    # Finalize the Master Vault
    builder.save("cartridges/pulse_master_v3_6")
    print("\n✅ Knowledge Rescue Complete!")
    print("Vault: cartridges/pulse_master_v3_6.hat | .tah")
    print("Status: All legacy assets linked to the v3.6 Intelligence Grid.")

if __name__ == "__main__":
    migrate_assets()
