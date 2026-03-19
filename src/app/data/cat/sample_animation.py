import argparse
import os
from pathlib import Path

import trimesh
import torch
import numpy as np
import pygltflib
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
from scipy.spatial.transform import Slerp
from cryo_sbi.wpa_simulator.image_generation import project_density

def get_data_from_accessor(glb, accessor_index):
    accessor = glb.accessors[accessor_index]
    buffer_view = glb.bufferViews[accessor.bufferView]
    buffer = glb.buffers[buffer_view.buffer]
    data = glb.get_data_from_buffer_uri(buffer.uri)
    
    dtype_map = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
    type_counts = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
    
    dt = dtype_map[accessor.componentType]
    shape = (accessor.count, type_counts[accessor.type])
    
    start = buffer_view.byteOffset + (accessor.byteOffset or 0)
    length = accessor.count * type_counts[accessor.type] * np.dtype(dt).itemsize
    
    stride = getattr(buffer_view, 'byteStride', None)
    if stride is None:
        arr = np.frombuffer(data[start:start+length], dtype=dt).reshape(shape)
    else:
        # properly read strided
        arr = np.ndarray((accessor.count,), dtype=[('v', dt, (shape[1],))], buffer=data[start:], strides=(stride,))['v']
    
    if type_counts[accessor.type] == 1:
        return arr.flatten()
    return arr

def trs_to_matrix(t, r, s):
    mat = np.eye(4)
    mat[:3, :3] = R.from_quat(r).as_matrix() * s
    mat[:3, 3] = t
    return mat

class GLBAnimator:
    """Evaluates skeletal skinning from a GLB animation at any given time t."""
    def __init__(self, filepath):
        self.glb = pygltflib.GLTF2().load(filepath)
        # Parse hierarchy: child -> parent map
        self.parent_map = {}
        for i, node in enumerate(self.glb.nodes):
            for child in (node.children or []):
                self.parent_map[child] = i
                
        # Parse animations
        self.anim_data = {} # node_idx -> {path -> (times, values)}
        if self.glb.animations:
            anim = self.glb.animations[0]
            for channel in anim.channels:
                sampler = anim.samplers[channel.sampler]
                times = get_data_from_accessor(self.glb, sampler.input)
                values = get_data_from_accessor(self.glb, sampler.output)
                if channel.target.node not in self.anim_data:
                    self.anim_data[channel.target.node] = {}
                self.anim_data[channel.target.node][channel.target.path] = (times, values)
        
        # Get time bounds
        self.t_min = 0.0
        self.t_max = 0.0
        for node_dict in self.anim_data.values():
            for t_arr, v_arr in node_dict.values():
                self.t_min = min(self.t_min, t_arr[0])
                self.t_max = max(self.t_max, t_arr[-1])

    def get_local_transform(self, node_idx, t):
        node = self.glb.nodes[node_idx]
        trans = np.array(node.translation or [0, 0, 0], dtype=float)
        rot = np.array(node.rotation or [0, 0, 0, 1], dtype=float)
        scale = np.array(node.scale or [1, 1, 1], dtype=float)
        
        if node_idx in self.anim_data:
            tracks = self.anim_data[node_idx]
            if "translation" in tracks:
                times, vals = tracks["translation"]
                trans = np.array([np.interp(t, times, vals[:, i]) for i in range(3)])
            if "scale" in tracks:
                times, vals = tracks["scale"]
                scale = np.array([np.interp(t, times, vals[:, i]) for i in range(3)])
            if "rotation" in tracks:
                times, vals = tracks["rotation"]
                # SLERP
                if t <= times[0]: rot = vals[0]
                elif t >= times[-1]: rot = vals[-1]
                else:
                    idx = np.searchsorted(times, t)
                    slerp = Slerp(times[idx-1:idx+1], R.from_quat(vals[idx-1:idx+1]))
                    rot = slerp([t])[0].as_quat()
        return trs_to_matrix(trans, rot, scale)
        
    def get_global_transform(self, node_idx, t, cache):
        if node_idx in cache:
            return cache[node_idx]
        loc = self.get_local_transform(node_idx, t)
        if node_idx in self.parent_map:
            par = self.get_global_transform(self.parent_map[node_idx], t, cache)
            glob = par @ loc
        else:
            glob = loc
        cache[node_idx] = glob
        return glob

    def get_skinned_mesh(self, t):
        mesh_node_idx = None
        for i, n in enumerate(self.glb.nodes):
            if n.mesh is not None:
                mesh_node_idx = i
                break
        
        mesh_idx = self.glb.nodes[mesh_node_idx].mesh
        mesh = self.glb.meshes[mesh_idx]
        prim = mesh.primitives[0]
        
        pos = get_data_from_accessor(self.glb, prim.attributes.POSITION)
        indices = get_data_from_accessor(self.glb, prim.indices).reshape(-1, 3)
        cache = {}
        mesh_global = self.get_global_transform(mesh_node_idx, t, cache)
        
        if hasattr(prim.attributes, 'JOINTS_0') and prim.attributes.JOINTS_0 is not None:
            joints = get_data_from_accessor(self.glb, prim.attributes.JOINTS_0)
            weights = get_data_from_accessor(self.glb, prim.attributes.WEIGHTS_0)
            
            skin_idx = self.glb.nodes[mesh_node_idx].skin
            skin = self.glb.skins[skin_idx]
            
            ibm_raw = get_data_from_accessor(self.glb, skin.inverseBindMatrices).reshape(-1, 4, 4)
            ibm = ibm_raw.transpose(0, 2, 1) # glTF matrices are column-major
            
            mesh_inv = np.linalg.inv(mesh_global)
            
            joint_mats = np.zeros((len(skin.joints), 4, 4))
            for i, j_idx in enumerate(skin.joints):
                j_global = self.get_global_transform(j_idx, t, cache)
                joint_mats[i] = mesh_inv @ j_global @ ibm[i]
            
            # apply skinning
            new_pos = np.zeros_like(pos)
            pos_h = np.column_stack([pos, np.ones(len(pos))])
            for i in range(len(pos)):
                mat = np.zeros((4, 4))
                for j in range(4):
                    weight = weights[i, j]
                    if weight > 0:
                        joint_idx = int(joints[i, j])
                        mat += weight * joint_mats[joint_idx]
                p = mat @ pos_h[i]
                new_pos[i] = p[:3] / p[3]
            pos = new_pos
            
        pos_h = np.column_stack([pos, np.ones(len(pos))])
        world_pos = (mesh_global @ pos_h.T).T[:, :3]
        return world_pos, indices


def farthest_point_sampling(points, num_samples):
    """
    Farthest Point Sampling (FPS) to ensure evenly spaced points 
    when extracting an exact number of samples.
    """
    N = points.shape[0]
    if num_samples >= N:
        return points
    
    selected_indices = np.zeros(num_samples, dtype=int)
    distances = np.ones(N) * np.inf
    
    # Randomly select the first point
    current_index = np.random.randint(0, N)
    selected_indices[0] = current_index
    
    for i in range(1, num_samples):
        current_point = points[current_index]
        dist_to_current = np.sum((points - current_point) ** 2, axis=1)
        distances = np.minimum(distances, dist_to_current)
        current_index = np.argmax(distances)
        selected_indices[i] = current_index
        
    return points[selected_indices]


def voxelize_and_sample(mesh, target_points=2500):
    print(f"Voxelizing frame to find ~{target_points} grid points...")
    min_pitch = np.max(mesh.extents) / 200.0
    max_pitch = np.max(mesh.extents) / 5.0
    
    best_points = None
    best_diff = float('inf')
    
    for _ in range(30):
        pitch = (min_pitch + max_pitch) / 2
        try:
            vox = mesh.voxelized(pitch=pitch).fill()
            points = vox.points
        except Exception:
            points = []
            
        n = len(points)
        if n >= target_points and (n - target_points) < best_diff:
            best_diff = n - target_points
            best_points = points
            
        if n > target_points:
            min_pitch = pitch
        else:
            max_pitch = pitch
            
    if best_points is None:
        best_points = mesh.voxelized(pitch=min_pitch).points

    points = best_points
    n_points = len(points)
    print(f"  Found grid with {n_points} points.")
    
    if n_points > target_points:
        points = farthest_point_sampling(points, target_points)
    elif n_points < target_points:
        # Pad by duplicating random points to guarantee exactly target_points
        print(f"  Padding {target_points - n_points} points via duplication.")
        pad_indices = np.random.choice(n_points, target_points - n_points, replace=True)
        points = np.vstack([points, points[pad_indices]])
    
    print(f"  Frame sampled to exactly {len(points)} points.")
    return points


def main():
    parser = argparse.ArgumentParser(description="Sample frames from a GLTF/GLB animation.")
    parser.add_argument("--num_models", type=int, default=5, help="Number of frames to sample (at least 2).")
    parser.add_argument("--target_points", type=int, default=2500, help="Number of points to sample per frame via voxelization.")
    args = parser.parse_args()
    
    SCRIPT_DIR = Path(__file__).resolve().parent
    
    # Robust dynamic path
    anim_file = SCRIPT_DIR / "cat_animation.gltf"
    if not anim_file.exists():
        for ext in ("*.gltf", "*.glb"):
            matches = list(SCRIPT_DIR.glob(ext))
            if matches:
                anim_file = matches[0]
                break
                
    if not anim_file.exists():
        print(f"Error: Could not find cat_animation.gltf or any .gltf/.glb file in {SCRIPT_DIR}")
        exit(1)
        
    anim_path = str(anim_file)
    num_models = max(2, args.num_models)
    target_points = args.target_points
    
    print(f"Loading GLB animation from {anim_path}...")
    animator = GLBAnimator(anim_path)
    print(f"Animation duration: {animator.t_max - animator.t_min:.2f}s")
    
    all_frame_points = []
    
    # Sample times from start to end inclusive
    times = np.linspace(animator.t_min, animator.t_max, num_models)
    
    for i, t in enumerate(times):
        print(f"\nProcessing Frame {i+1}/{num_models} (Time: {t:.3f}s)")
        v, f = animator.get_skinned_mesh(t)
        mesh = trimesh.Trimesh(vertices=v, faces=f)
        
        points = voxelize_and_sample(mesh, target_points)
        all_frame_points.append(points)
        
    tensor_points = torch.tensor(np.array(all_frame_points), dtype=torch.float32)
    # Shape becomes (num_models, 3, target_points)
    tensor_points = tensor_points.permute(0, 2, 1)
    
    anim_name = anim_file.stem
    
    pt_path = SCRIPT_DIR / f"cat_points_grid_{anim_name}_{num_models}models.pt"
    torch.save(tensor_points, str(pt_path))
    print(f"\nSaved PyTorch tensor of shape {tensor_points.shape} to {pt_path.name}")
    
    # Save a combined point cloud for 3D viewing to visualize all frames
    #combined_points = np.vstack(all_frame_points)
    #pc = trimesh.PointCloud(combined_points)
    #ply_path = SCRIPT_DIR / f"cat_points_grid_{anim_name}_{num_models}models.ply"
    #pc.export(str(ply_path))
    #print(f"Saved combined animated point cloud to {ply_path.name} for 3D viewing.")
    
    # Generate Sanity Check Clean Projections
    print("\nGenerating 5 clean projections per model as a sanity check...")
    num_pixels = torch.tensor(128.0)
    pixel_size = torch.tensor(2.0)
    sigma = torch.tensor([2.0])
    shift = torch.tensor([[0.0, 0.0]])
    
    # Scale and center logic consistently applied to everything for visualization
    # We center based on the overall mean and scale by overall max uniformly to preserve animation relative motion
    all_points_np = np.array(all_frame_points)
    global_mean = np.mean(all_points_np, axis=(0, 1))
    all_points_centered = all_points_np - global_mean
    global_max = np.max(np.abs(all_points_centered))
    all_points_scaled = (all_points_centered / global_max) * 100.0
    
    fig, axes = plt.subplots(num_models, 5, figsize=(15, 3 * num_models))
    if num_models == 1:
        axes = [axes] # ensure 2D indexing works
    
    for i in range(num_models):
        coords = torch.from_numpy(all_points_scaled[i]).T.unsqueeze(0).float()
        for j in range(5):
            # Generate random quaternion
            quat_np = R.random().as_quat() # [x, y, z, w]
            quat = torch.tensor([quat_np]).float()
            
            clean_proj = project_density(coords, quat, sigma, shift, num_pixels, pixel_size)
            
            ax = axes[i][j]
            ax.imshow(clean_proj[0].detach().cpu().numpy(), cmap='gray')
            ax.set_title(f"M{i} P{j}")
            ax.axis('off')

    plt.tight_layout()
    proj_path = SCRIPT_DIR / f"cat_sanity_projections_{anim_name}_{num_models}models.png"
    plt.savefig(str(proj_path))
    print(f"Saved {num_models * 5} clean projections to {proj_path.name}")

if __name__ == "__main__":
    main()
