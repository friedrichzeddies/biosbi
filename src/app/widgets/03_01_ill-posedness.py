import streamlit as st
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.transform import Rotation as R
import os

from cryo_sbi.wpa_simulator.cryo_em_simulator import cryo_em_simulator, CryoEmSimulator
import cryo_sbi.utils.estimator_utils as est_utils

# Base paths for the specific ResNet model
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "models", "2cat_resnet")
SIM_JSON = os.path.join(BASE_DIR, "simulation_parameters.json")
TRAIN_JSON = os.path.join(BASE_DIR, "training_parameters.json")
ESTIMATOR_PT = os.path.join(BASE_DIR, "estimator.pt")

# Set page config
st.set_page_config(page_title="Ill-Posedness Conformations", layout="wide")

@st.cache_resource
def load_assets():
    simulator = CryoEmSimulator(SIM_JSON, device="cpu")
    posterior = est_utils.load_estimator(
        TRAIN_JSON, 
        ESTIMATOR_PT, 
        device="cpu"
    )
        
    return simulator, posterior

simulator, posterior = load_assets()

from cryo_sbi.wpa_simulator.image_generation import project_density

def generate_image_for_model(simulator, model_idx, rot_x, rot_y, rot_z):
    """Generates a proper base image directly from the simulator core logic using manual injection."""
    # 1. Base parameters sampled from prior
    parameters = simulator._priors.sample((1,))
    
    # 2. Override index to deterministic value
    idx_tensor = torch.tensor([[model_idx]], dtype=torch.float32)
    
    # 3. Override quaternion based on 3D sliders
    quat_np = R.from_euler('xyz', [rot_x, rot_y, rot_z], degrees=True).as_quat()
    quat_tensor = torch.tensor([quat_np], dtype=torch.float32)
    
    # Build batch parameters exactly as cryo_em_simulator expects
    batch_params = [
        idx_tensor,
        quat_tensor,
        parameters[2], # sigma
        parameters[3], # shift
        parameters[4], # defocus
        parameters[5], # b_factor
        parameters[6], # amp
        parameters[7], # snr
    ]
    
    noisy_img = cryo_em_simulator(
        simulator._models,
        *batch_params,
        simulator._num_pixels,
        simulator._pixel_size
    )
    
    # Generate the clean underlying density (before CTF and Noise)
    clean_img = project_density(
        simulator._models[[model_idx]],
        quat_tensor,
        parameters[2],
        parameters[3],
        simulator._num_pixels,
        simulator._pixel_size
    )
    
    return noisy_img, clean_img

@st.fragment
def render_ui():
    st.title("Ill-Posedness: Ambiguous Conformations")
    st.markdown("""
        See how two completely different 3D conformations (Standing vs Lying) can produce indistinguishable 2D pictures from specific angles. 
        We then query the SBI posterior to see if it successfully handles this ambiguity by assigning high probability to both models.
    """)
    
    # 1. Compact Controls Row
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1.5, 1, 1, 1])
    with ctrl1:
        st.write("") # Spacer
        overlay_clean = st.checkbox("Overlay Clean Density", value=False)
    with ctrl2:
        rot_x = st.slider("Rot X °", 0, 360, 0, key="x")
    with ctrl3:
        rot_y = st.slider("Rot Y °", 0, 360, 45, key="y")
    with ctrl4:
        rot_z = st.slider("Rot Z °", 0, 360, 0, key="z")
        
    # 2. Compact Images Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Conformation 0: Standing**")
        img_noisy_1, img_clean_1 = generate_image_for_model(simulator, 0, rot_x, rot_y, rot_z)
        
        fig1, ax1 = plt.subplots(figsize=(3, 3))
        ax1.imshow(img_noisy_1[0].numpy(), cmap='gray')
        if overlay_clean:
            clean_np = img_clean_1[0].numpy()
            masked_clean = np.ma.masked_where(clean_np < clean_np.max() * 0.1, clean_np)
            ax1.imshow(masked_clean, cmap='hot', alpha=0.5)
        ax1.axis('off')
        st.pyplot(fig1)
        
    with col2:
        st.write("**Conformation 1: Lying Down**")
        img_noisy_2, img_clean_2 = generate_image_for_model(simulator, 1, rot_x, rot_y, rot_z)
        
        fig2, ax2 = plt.subplots(figsize=(3, 3))
        ax2.imshow(img_noisy_2[0].numpy(), cmap='gray')
        if overlay_clean:
            clean_np2 = img_clean_2[0].numpy()
            masked_clean2 = np.ma.masked_where(clean_np2 < clean_np2.max() * 0.1, clean_np2)
            ax2.imshow(masked_clean2, cmap='hot', alpha=0.5)
        ax2.axis('off')
        st.pyplot(fig2)
        
    st.divider()
    
    # 3. Compact Inference Plot Overlaying both results
    with st.spinner("Evaluating Posterior using the CNN Estimator..."):
        images_batch = torch.cat([img_noisy_1, img_noisy_2], dim=0)
        samples = est_utils.sample_posterior(
            estimator=posterior,
            images=images_batch,
            num_samples=1000,
            batch_size=1000,
            device="cpu"
        )
        if samples.ndim == 2:
            if samples.shape[0] == 2:
                s1, s2 = samples[0, :].detach().numpy(), samples[1, :].detach().numpy()
            else:
                s1, s2 = samples[:, 0].detach().numpy(), samples[:, 1].detach().numpy()
        else:
            if samples.shape[0] == 2:
                s1, s2 = samples[0, :, 0].detach().numpy(), samples[1, :, 0].detach().numpy()
            else:
                s1, s2 = samples[:, 0, 0].detach().numpy(), samples[:, 1, 0].detach().numpy()
                
    fig, ax = plt.subplots(figsize=(10, 2.5))
    sns.kdeplot(s1, ax=ax, fill=True, color="#1f77b4", label="Inferred from Standing Image", warn_singular=False)
    sns.kdeplot(s2, ax=ax, fill=True, color="#ff7f0e", label="Inferred from Lying Image", warn_singular=False)
    
    ax.set_title("Posterior Probability: Which Conformation generated the image?")
    ax.set_xlim(-0.5, 1.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["0: Standing", "1: Lying Down"])
    ax.legend(loc="upper right")
    ax.set_ylabel("Density")
    
    st.pyplot(fig)

render_ui()
