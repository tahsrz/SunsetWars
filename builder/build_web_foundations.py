import sys
import os
from swarm_builder import SwarmMemoriaBuilder

def build_web_foundations():
    builder = SwarmMemoriaBuilder()
    
    # --- NEXT.JS 15 SECTOR ---
    
    # 1. Next.js 15 Overview
    next15_text = (
        "Next.js 15: The Server-First Framework. "
        "Built on a model where everything is a Server Component (RSC) by default. "
        "Major changes: fetch requests are now dynamic (no cache) by default. "
        "Key files: layout.tsx (persistent UI), page.tsx (route UI), loading.tsx (Suspense), error.tsx (Error Boundary)."
    )
    next15_off = builder.add_swarm_shard(next15_text)
    builder.register_symbol("NEXTJS_15_CORE", next15_off)
    
    # 2. React Server Components (RSC)
    rsc_text = (
        "React Server Components (RSC): Components that run only on the server and send zero JS to the browser. "
        "RSC can be async/await for direct DB/file-system access. "
        "Client Components ('use client') are used only for interactivity and hydration. "
        "Rule: You cannot import Server Components into Client Components, but you can pass them as children."
    )
    rsc_off = builder.add_swarm_shard(rsc_text, symbols=["NEXTJS_15_CORE"])
    builder.register_symbol("RSC_PROTOCOL", rsc_off)
    
    # 3. Server Actions
    actions_text = (
        "Server Actions ('use server'): Async functions that execute on the server, typically for mutations. "
        "Can be called from both Server and Client components. "
        "Primary way to handle form submissions (POST/PUT/DELETE) without manually managing API routes."
    )
    actions_off = builder.add_swarm_shard(actions_text, symbols=["RSC_PROTOCOL"])
    builder.register_symbol("SERVER_ACTIONS", actions_off)

    # --- TAILWIND CSS V4 SECTOR ---

    # 4. Tailwind CSS v4
    tailwind4_text = (
        "Tailwind CSS v4: Powered by the Oxide Engine (Rust). "
        "5x faster full builds. CSS-First Configuration: Use @theme block in CSS instead of tailwind.config.js. "
        "Native Cascade Layers (@layer) and support for modern CSS: @container queries, color-mix(), and 3D transforms."
    )
    tw4_off = builder.add_swarm_shard(tailwind4_text)
    builder.register_symbol("TAILWIND_4", tw4_off)

    # --- FRAMER MOTION SECTOR ---

    # 5. High-Performance Motion
    motion_text = (
        "Framer Motion (Motion): High-performance animation for React. "
        "Performance rule: Only animate GPU-accelerated properties (x, y, scale, rotate, opacity). "
        "Optimization: Use LazyMotion with 'm' components to reduce bundle size by ~25kb. "
        "Use Motion Values (useMotionValue) for scroll/drag updates to bypass React re-renders."
    )
    motion_off = builder.add_swarm_shard(motion_text, symbols=["NEXTJS_15_CORE"])
    builder.register_symbol("FRAMER_MOTION_OPS", motion_off)

    # 6. Hybrid Patterns: Tailwind + Motion
    hybrid_text = (
        "Hybrid UI Patterns: Next.js Server Components for layout, Framer Motion 'm' components for interaction. "
        "Tailwind v4 CSS variables can be passed directly to Framer Motion animate props: animate={{ color: 'var(--color-brand)' }}. "
        "Use 'willChange' hint for complex 3D transforms."
    )
    hybrid_off = builder.add_swarm_shard(hybrid_text, symbols=["TAILWIND_4", "FRAMER_MOTION_OPS"])
    builder.register_symbol("HYBRID_PATTERNS", hybrid_off)

    # Save the cartridge
    builder.save_prototype("cartridges/web_foundations")
    print("Web Foundations Cartridge Compiled (v3.5 Swarm Protocol).")

if __name__ == "__main__":
    # Ensure builder is in path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    build_web_foundations()
