import os
import streamlit as st
import numpy as np
import torch
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
from cryo_sbi.wpa_simulator.cryo_em_simulator import CryoEmSimulator
from cryo_sbi.wpa_simulator.image_generation import project_density

# Define base directory relative to this file
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "Chapter 2 - BioEM")

@st.cache_resource
def load_simulator():
    sim_json = os.path.join(BASE_DIR, "cat_proj_params.json")
    # Initialize the simulator on CPU
    return CryoEmSimulator(sim_json, device="cpu")

def create_donut_mask(shape, inner_radius, outer_radius):
    """Creates a boolean mask for a given shape centered at N//2."""
    N = shape[0]
    Y, X = np.ogrid[:N, :N]
    center_y, center_x = N // 2, N // 2
    dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    return (dist_from_center >= inner_radius) & (dist_from_center <= outer_radius)

@st.fragment
def render():
    st.write("#### 2D Fourier Transform")
    st.write("Explore how different spatial frequencies (low vs. high) contribute to the image formation.")
    
    simulator = load_simulator()
    
    # 1. Controls configuration
    col_controls1, col_controls2 = st.columns(2)
    
    with col_controls1:
        st.write("#### Projection Orientation")
        rot_x = st.slider("Rot X", -180, 180, -90, key="widget_fourier_rot_x")
        rot_y = st.slider("Rot Y", -180, 180, 0, key="widget_fourier_rot_y")
        rot_z = st.slider("Rot Z", -180, 180, 0, key="widget_fourier_rot_z")
        
    with col_controls2:
        st.write("#### Fourier Mask Settings")
        preset = st.selectbox(
            "Presets", 
            ["Custom", "Full Spectrum", "Low-Pass (Blur)", "High-Pass (Edges)", "Band-Pass (Details)"],
            key="widget_fourier_preset"
        )
        
        # Max radius is roughly N/2
        N = int(simulator._num_pixels.item())
        max_rad = N // 2
        
        if preset == "Full Spectrum":
            in_rad, out_rad = 0.0, float(max_rad)
        elif preset == "Low-Pass (Blur)":
            in_rad, out_rad = 0.0, float(max_rad * 0.25)
        elif preset == "High-Pass (Edges)":
            in_rad, out_rad = float(max_rad * 0.25), float(max_rad)
        elif preset == "Band-Pass (Details)":
            in_rad, out_rad = float(max_rad * 0.15), float(max_rad * 0.4)
        else:
            in_rad = st.slider("Inner Radius", 0.0, float(max_rad), 0.0, key="widget_fourier_in_rad")
            out_rad = st.slider("Outer Radius", 0.0, float(max_rad), float(max_rad), key="widget_fourier_out_rad")
            
            # Enforce logical constraint
            if in_rad > out_rad:
                st.warning("Inner Radius cannot be larger than Outer Radius. Adjusting...")
                in_rad = out_rad
    
    # 2. Generate Projection
    # Generate clean image (index 0 for standing cat)
    quat_tensor = torch.tensor([R.from_euler('xyz', [rot_x, rot_y, rot_z], degrees=True).as_quat()], dtype=torch.float32)
    
    # Sample default parameters for everything else
    parameters = simulator._priors.sample((1,))
    sigma = parameters[2]
    shift = parameters[3]
    
    clean_img_tensor = project_density(
        simulator._models[[0]], 
        quat_tensor, 
        sigma, 
        shift, 
        simulator._num_pixels, 
        simulator._pixel_size
    )
    
    # Squeeze out batch and channel dims -> 2D numpy array
    img_real = clean_img_tensor[0].detach().cpu().numpy()
    
    # 3. Compute 2D Fourier Transform
    fft_complex = np.fft.fft2(img_real)
    fft_shifted = np.fft.fftshift(fft_complex)
    
    # Power spectrum for vis (log scale)
    power_spectrum = np.log(np.abs(fft_shifted) + 1e-8)
    
    # 4. Apply Mask
    mask = create_donut_mask(img_real.shape, in_rad, out_rad)
    fft_shifted_masked = fft_shifted * mask
    
    # Masked Power spectrum for vis
    # We overlay the masked areas with 0 or just plot the masked power spectrum.
    # To keep the colors consistent, we plot the masked version but keep vmin/vmax tight
    power_spectrum_masked = np.log(np.abs(fft_shifted_masked) + 1e-8)
    # Give the masked out region a specific low value for contrast
    min_val = np.min(power_spectrum)
    power_spectrum_masked[~mask] = min_val
    
    # 5. Inverse FFT
    fft_unshifted = np.fft.ifftshift(fft_shifted_masked)
    img_filtered_complex = np.fft.ifft2(fft_unshifted)
    img_filtered = np.real(img_filtered_complex) # Discard tiny numerical imaginary parts
    
    # 6. Visualization
    st.write("---")
    col1, col2, col3 = st.columns(3)
    
    def plot_image(ax, data, title, cmap='gray', **kwargs):
        ax.imshow(data, cmap=cmap, **kwargs)
        ax.set_title(title)
        ax.axis('off')
        
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Normalize real space image slightly for display
    vmin_img, vmax_img = np.percentile(img_real, 1), np.percentile(img_real, 99)
    
    plot_image(axes[0], img_real, "Original Projection", vmin=vmin_img, vmax=vmax_img)
    
    # For power spectrum, maintain fixed scale relative to unmasked
    vmin_ps, vmax_ps = np.percentile(power_spectrum, 5), np.max(power_spectrum)
    plot_image(axes[1], power_spectrum_masked, "Masked Power Spectrum", cmap='viridis', vmin=vmin_ps, vmax=vmax_ps)
    
    # Draw simple circles to emphasize the mask boundaries if not full spectrum
    if in_rad > 0:
        circle_in = plt.Circle((N//2, N//2), in_rad, color='red', fill=False, linestyle='--', alpha=0.5)
        axes[1].add_patch(circle_in)
    if out_rad < max_rad:
        circle_out = plt.Circle((N//2, N//2), out_rad, color='red', fill=False, linestyle='--', alpha=0.5)
        axes[1].add_patch(circle_out)
        
    # The filtered image can have different scale, typically smaller dynamic range if high-passed
    plot_image(axes[2], img_filtered, "Filtered Projection")
    
    plt.tight_layout()
    st.pyplot(fig)
    
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
