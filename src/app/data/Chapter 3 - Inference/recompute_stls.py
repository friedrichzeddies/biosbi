import sys
import os
import matplotlib.pyplot as plt
import trimesh
import trimesh.transformations as tf
import numpy as np

# Dynamically add src to path to import GLBAnimator
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from app.data.cat.sample_animation import GLBAnimator

def main():
    anim_path = os.path.join(SRC_DIR, 'app', 'data', 'cat', 'cat_animation.gltf')
    out_dir = os.path.join(SCRIPT_DIR, 'cat_conformations')
    os.makedirs(out_dir, exist_ok=True)

    print(f"Loading GLB animation from {anim_path}...")
    animator = GLBAnimator(anim_path)
    times = np.linspace(animator.t_min, animator.t_max, 10)

    # ---------------------------------------------------------
    # TWEAK YOUR DESIRED COMPOUND ROTATION MATRICES HERE:
    # Use np.radians(degrees). For example, 90, 180, -90, 45, etc.
    # ---------------------------------------------------------
    R1 = tf.rotation_matrix(np.radians(90), [1, 0, 0])  # Rotate around X-axis
    R2 = tf.rotation_matrix(np.radians(120), [0, 1, 0])  # Rotate around Y-axis
    R3 = tf.rotation_matrix(np.radians(90), [0, 0, 1])  # Rotate around Z-axis
    
    # Map current XY plane to XZ plane:
    R4 = tf.rotation_matrix(np.radians(90), [1, 0, 0])  # Rotate around X-axis
    
    # Combined sequence
    R_total = R4 @ R3 @ R2 @ R1

    first_mesh_vertices = None

    print(f"Extracting frames and applying total rotation matrix...")
    for idx, t in enumerate(times):
        v, f = animator.get_skinned_mesh(t)
        mesh = trimesh.Trimesh(vertices=v, faces=f)
        
        # Apply the final rotation sequence to the mesh
        mesh.apply_transform(R_total)
        
        # Save explicitly
        out_file = os.path.join(out_dir, f'cat_conformation_{idx+1:02d}.stl')
        mesh.export(out_file, file_type='stl')
        print(f"  -> Saved {os.path.basename(out_file)}")
        
        if idx == 0:
            first_mesh_vertices = mesh.vertices.copy()

    # ---------------------------------------------------------
    # Generate Sanity Check 2D Viewing Planes
    # ---------------------------------------------------------
    print("\nGenerating Sanity Check Plot for Conformation 1...")
    
    # We plot the point cloud of vertices from 3 orthogonal planes
    pts = first_mesh_vertices[::5] # Subsample for drawing performance
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # View 1: Looking down Z-axis (Top down: XY plane)
    axes[0].scatter(x, y, s=2, alpha=0.5, c='b')
    axes[0].set_xlabel("X-axis")
    axes[0].set_ylabel("Y-axis")
    axes[0].set_title("XY Plane (Looking down Z)")
    axes[0].axis('equal')
    
    # View 2: Looking down Y-axis (XZ plane)
    axes[1].scatter(x, z, s=2, alpha=0.5, c='g')
    axes[1].set_xlabel("X-axis")
    axes[1].set_ylabel("Z-axis")
    axes[1].set_title("XZ Plane (Looking down Y)")
    axes[1].axis('equal')
    
    # View 3: Looking down X-axis (YZ plane)
    axes[2].scatter(y, z, s=2, alpha=0.5, c='r')
    axes[2].set_xlabel("Y-axis")
    axes[2].set_ylabel("Z-axis")
    axes[2].set_title("YZ Plane (Looking down X)")
    axes[2].axis('equal')
    
    for ax in axes:
        ax.grid(True, linestyle='--', alpha=0.6)
        
    plt.tight_layout()
    plot_out = os.path.join(SCRIPT_DIR, 'rotation_sanity_check.png')
    plt.savefig(plot_out, dpi=150)
    print(f"Saved sanity check visualization to {plot_out}")

if __name__ == "__main__":
    main()
