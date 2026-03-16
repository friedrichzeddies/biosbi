import trimesh
import torch
import numpy as np

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
        # Update distances
        current_point = points[current_index]
        dist_to_current = np.sum((points - current_point) ** 2, axis=1)
        distances = np.minimum(distances, dist_to_current)
        
        # Select the farthest point
        current_index = np.argmax(distances)
        selected_indices[i] = current_index
        
    return points[selected_indices]

def main():
    obj_path = "/Users/sebastianmetzler/Downloads/Cat/12221_Cat_v1_l3.obj"
    print(f"Loading mesh from {obj_path}...")
    mesh = trimesh.load(obj_path)
    
    print("Voxelizing to find grid points...")
    # Binary search for voxel pitch that yields slightly more than 2000 points
    target_points = 2500
    min_pitch = np.max(mesh.extents) / 200.0
    max_pitch = np.max(mesh.extents) / 5.0
    
    best_points = None
    best_diff = float('inf')
    
    # We want a grid that gives >= 2000 points so we can downsample exactly
    for _ in range(20):
        pitch = (min_pitch + max_pitch) / 2
        try:
            # Voxelize the mesh
            vox = mesh.voxelized(pitch=pitch)
            # Fill the hollow voxel volume since mesh is not watertight
            vox = vox.fill()
            points = vox.points
        except Exception as e:
            points = []
            
        n = len(points)
        
        if n >= target_points and (n - target_points) < best_diff:
            best_diff = n - target_points
            best_points = points
            
        if n > target_points:
            min_pitch = pitch  # pitch too small, too many points
        else:
            max_pitch = pitch  # pitch too large, too few points

    # Fallback if no grid is perfectly >= 2000 (rare, but just in case)
    if best_points is None:
        best_points = mesh.voxelized(pitch=min_pitch).points

    points = best_points
    n_points = len(points)
    print(f"Found grid with {n_points} points.")
    
    # FPS down to exactly 2000 points to maintain the 'even spacing' 
    # while meeting the exact point count requirement
    if n_points > target_points:
        print(f"Applying Farthest Point Sampling to get exactly {target_points} points...")
        points = farthest_point_sampling(points, target_points)
    
    print(f"Final point count: {len(points)}")
    
    # Save as .ply for 3D viewing 
    pc = trimesh.PointCloud(points)
    ply_path = "cat_points_grid.ply"
    pc.export(ply_path)
    print(f"Saved point cloud to {ply_path} for 3D viewing (open with MeshLab, Blender, etc.)")
    
    # Save as PyTorch tensor
    pt_path = "cat_points_grid.pt"
    tensor_points = torch.tensor(points, dtype=torch.float32).unsqueeze(0).permute(0,2,1)
    torch.save(tensor_points, pt_path)
    print(f"Saved PyTorch tensor of shape {tensor_points.shape} to {pt_path}")

if __name__ == "__main__":
    main()
