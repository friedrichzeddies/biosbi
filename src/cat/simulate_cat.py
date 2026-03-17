import torch
import numpy as np
import matplotlib.pyplot as plt
from cryo_sbi.wpa_simulator.image_generation import project_density
from cryo_sbi.wpa_simulator.ctf import apply_ctf
from cryo_sbi.wpa_simulator.noise import add_noise
from cryo_sbi.wpa_simulator.normalization import gaussian_normalize_image

def main():
    pt_path = "cat_points_grid.pt"
    print(f"Loading sampled points from {pt_path}...")
    # Load tensor and convert to numpy array to match existing processing
    sampled_vertices = torch.load(pt_path, weights_only=True).numpy()
    
    # Center the model
    sampled_vertices -= np.mean(sampled_vertices, axis=0)
    
    # Scale it to fit reasonably in a box (let's say 100A)
    max_dim = np.max(np.abs(sampled_vertices))
    sampled_vertices = (sampled_vertices / max_dim) * 100.0  # Scale to ~100A total width
    
    # Convert to expected tensor shape (1, 3, N)
    coords = torch.from_numpy(sampled_vertices).T.unsqueeze(0).float()
    
    # Simulation Parameters
    num_pixels = torch.tensor(128.0)
    pixel_size = torch.tensor(2.0)
    sigma = torch.tensor([2.0]) # Gaussian blur width
    shift = torch.tensor([[0.0, 0.0]]) # No shift for now
    
    # Generate random quaternion for rotation
    # Let's just pick a nice view - roughly 45 deg rotation
    quat = torch.tensor([[0.728, 0.328, 0.5, -0.3]]) 

    print("Generating projection...")
    # 1. Project Density
    clean_projection = project_density(
        coords,
        quat,
        sigma,
        shift,
        num_pixels,
        pixel_size
    )

    # 2. Apply CTF (realistic params)
    defocus = torch.tensor([2.0])  # micrometers
    b_factor = torch.tensor([1.0])
    amp = torch.tensor([0.1])
    image_ctf = apply_ctf(clean_projection, defocus, b_factor, amp, pixel_size)

    # 3. Add Noise (low SNR for realism)
    snr = 0.5
    image_noisy = add_noise(image_ctf, snr)

    # 4. Normalize
    image_final = gaussian_normalize_image(image_noisy)

    # Visualization
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    axes[0].imshow(clean_projection[0].detach().cpu().numpy()*10, cmap='gray')
    axes[0].set_title("Clean Projection (Cat)")
    
    axes[1].imshow(image_ctf[0].detach().cpu().numpy(), cmap='gray')
    axes[1].set_title("With CTF")
    
    axes[2].imshow(image_final[0].detach().cpu().numpy(), cmap='gray')
    axes[2].set_title("Simulated Cryo-EM Image (SNR=0.5)")

    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])

    output_path = "cat_simulation_results.png"
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
