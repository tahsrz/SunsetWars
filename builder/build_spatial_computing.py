import sys
import os
from swarm_builder import SwarmMemoriaBuilder

def build_spatial_computing():
    builder = SwarmMemoriaBuilder()
    
    # --- THREE.JS PERFORMANCE SECTOR ---
    
    # 1. Draw Call & Mesh Management
    perf_text = (
        "Three.js Optimization: Maintain <100 draw calls per frame. "
        "Use InstancedMesh for duplicate geometries (buildings, foliage) and BatchedMesh for mixed static geometries. "
        "Mandatory: Call .dispose() on geometries, materials, and textures to prevent GPU memory leaks. "
        "Textures: Prefer KTX2 (Basis Universal) and Power-of-Two (POT) dimensions for mipmapping efficiency."
    )
    perf_off = builder.add_swarm_shard(perf_text)
    builder.register_symbol("THREEJS_PERF_OPS", perf_off)
    
    # --- SPATIAL MATH & ROTATION ---
    
    # 2. Quaternions & Matrix Decomposition
    math_text = (
        "Spatial Math: Avoid Euler angles to prevent Gimbal Lock. Use THREE.Quaternion for all rotations. "
        "Interpolation: Use .slerp() for smooth orientation changes. "
        "Matrix Ops: Use matrix.decompose(pos, quat, scale) to extract transforms. "
        "Culling: Manual frustum culling via camera.frustum.containsPoint() for large-scale procedural data."
    )
    math_off = builder.add_swarm_shard(math_text)
    builder.register_symbol("SPATIAL_MATH_CORE", math_off)
    
    # --- SHADER ARCHITECTURE (GLSL) ---
    
    # 3. GLSL Optimization
    glsl_text = (
        "GLSL Shaders: Avoid branching (if/else). Use step(), mix(), and smoothstep() for mathematical conditionals. "
        "Precision: lowp for colors, mediump for simple UVs, highp only for positions/depth. "
        "Varying management: Interpolation between vertex and fragment shaders is expensive; minimize varying usage."
    )
    glsl_off = builder.add_swarm_shard(glsl_text, symbols=["THREEJS_PERF_OPS"])
    builder.register_symbol("GLSL_SHADER_PROTOCOL", glsl_off)

    # --- SPATIAL INDEXING ---

    # 4. Octree vs. BVH
    indexing_text = (
        "Spatial Indexing: BVH (Bounding Volume Hierarchy) is standard for complex raycasting/picking (use three-mesh-bvh). "
        "Octrees are best for sparse 3D point-clouds. "
        "Spatial Hashing: O(1) constant-time neighbor lookups for uniform dynamic objects (particles/boids)."
    )
    indexing_off = builder.add_swarm_shard(indexing_text, symbols=["SPATIAL_MATH_CORE"])
    builder.register_symbol("SPATIAL_INDEXING_MODELS", indexing_off)

    # 5. Hybrid Integration: Rotoscope + Spatial
    hybrid_text = (
        "Hybrid Spatial Pattern: Integrate Rotoscope SAM 2 masks as dynamic textures or sprites. "
        "Use Raycasting (BVH optimized) to project mouse/touch coordinates onto the 3D 'TacticalCloth' mesh. "
        "Apply physics forces programmatically using the mesh vertex data extracted via Matrix decomposition."
    )
    hybrid_off = builder.add_swarm_shard(hybrid_text, symbols=["GLSL_SHADER_PROTOCOL", "SPATIAL_INDEXING_MODELS"])
    builder.register_symbol("SPATIAL_HYBRID_PATTERNS", hybrid_off)

    # Save the cartridge
    builder.save_prototype("cartridges/spatial_computing")
    print("Spatial Computing Cartridge Compiled (v3.5 Swarm Protocol).")

if __name__ == "__main__":
    # Ensure builder is in path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    build_spatial_computing()
