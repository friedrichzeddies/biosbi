import streamlit as st
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.transform import Rotation as R
import os
import json

from cryo_sbi.wpa_simulator.cryo_em_simulator import cryo_em_simulator, CryoEmSimulator
import cryo_sbi.utils.estimator_utils as est_utils

@st.cache_resource
def load_assets(model_dir):
    sim_json = os.path.join(model_dir, "simulation_parameters.json")
    train_json = os.path.join(model_dir, "training_parameters.json")
    estimator_pt = os.path.join(model_dir, "estimator.pt")
    
    simulator = CryoEmSimulator(sim_json, device="cpu")
    
    posterior = None
    # Gracefully decouple inference so users can still look at the simulation images even without a saved estimator
    if os.path.exists(train_json) and os.path.exists(estimator_pt):
        try:
            posterior = est_utils.load_estimator(
                train_json, 
                estimator_pt, 
                device="cpu"
            )
        except Exception as e:
            print(f"Failed to load posterior: {e}")
            
    return simulator, posterior

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
        See how different 3D conformations can produce indistinguishable 2D pictures from specific angles. 
        We then query the SBI posterior to see if it successfully handles this ambiguity by assigning valid probabilities.
    """)
    
    models_base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "models")
    if os.path.exists(models_base_dir):
        available_models = sorted([d for d in os.listdir(models_base_dir) if os.path.isdir(os.path.join(models_base_dir, d))])
    else:
        available_models = ["10cat_large_batch_resnet"]
        
    selected_model_name = st.selectbox("Select Cached Estimator Model", available_models)
    model_dir = os.path.join(models_base_dir, selected_model_name)
    
    try:
        simulator, posterior = load_assets(model_dir)
        num_models = len(simulator._models)
        
        train_params = {}
        train_json = os.path.join(model_dir, "training_parameters.json")
        if os.path.exists(train_json):
            with open(train_json, 'r') as f:
                train_params = json.load(f)
    except Exception as e:
        st.error(f"Failed to load simulator parameters for {selected_model_name}: {e}")
        return

    st.write(f"**Loaded Models:** {num_models} active conformations detected. *(Training Theta Shift: {train_params.get('THETA_SHIFT', 'N/A')}, Scale: {train_params.get('THETA_SCALE', 'N/A')})*")
    
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
        
    # 2. Dynamic Images Row (Only First and Last)
    indices_to_show = [0, num_models - 1] if num_models > 1 else [0]
    cols = st.columns(len(indices_to_show))
    images_noisy_list = []
    
    for c_idx, col in zip(indices_to_show, cols):
        with col:
            st.write(f"**Conformation {c_idx}**")
            n_img, c_img = generate_image_for_model(simulator, c_idx, rot_x, rot_y, rot_z)
            images_noisy_list.append(n_img)
            
            fig, ax = plt.subplots(figsize=(3, 3))
            ax.imshow(n_img[0].numpy(), cmap='gray')
            if overlay_clean:
                clean_np = c_img[0].numpy()
                masked_clean = np.ma.masked_where(clean_np < clean_np.max() * 0.1, clean_np)
                ax.imshow(masked_clean, cmap='hot', alpha=0.5)
            ax.axis('off')
            st.pyplot(fig)
            
    st.divider()
    
    # 3. Dynamic Inference Block
    if posterior is None:
        st.info("⚠️ No valid `estimator.pt` or `training_parameters.json` found in this model directory! Train an SBI Neural Flow to unlock posterior inference plotting.")
        return
        
    with st.spinner(f"Evaluating Posterior across {len(indices_to_show)} images..."):
        images_batch = torch.cat(images_noisy_list, dim=0)
        samples = est_utils.sample_posterior(
            estimator=posterior,
            images=images_batch,
            num_samples=1000,
            batch_size=1000,
            device="cpu"
        )
        
        # Standardize samples shape mapping
        # returns [batch_n, num_samples, n_params]
        model_samples = []
        num_inferences = len(indices_to_show)
        for i in range(num_inferences):
            if samples.ndim == 2:
                s = samples[i, :] if samples.shape[0] == num_inferences else samples[:, i]
            else:
                s = samples[i, :, 0] if samples.shape[0] == num_inferences else samples[:, i, 0]
            model_samples.append(s.detach().numpy())
            
    # Visual Layout
    plot_col1, plot_col2 = st.columns([2, 1])
    
    with plot_col1:
        fig1, ax1 = plt.subplots(figsize=(8, 3))
        
        # Iterate dynamic KDEs matching each evaluated base
        colors = plt.cm.tab10.colors
        for i, c_idx in enumerate(indices_to_show):
            c = colors[c_idx % len(colors)]
            sns.kdeplot(model_samples[i], ax=ax1, fill=True, color=c, label=f"Inferred from Conf {c_idx}", warn_singular=False)
            
        ax1.set_title("Continuous Posterior Density (with De-Quantization Boundaries)")
        ax1.set_xlim(-0.5, num_models - 0.5)
        
        # Dynamically build ticks at both the integer centers and fractional boundaries
        ticks = []
        labels = []
        for i in range(num_models):
            # Left boundary
            ticks.append(i - 0.5)
            labels.append(f"{i - 0.5}")
            
            # Center integer
            ticks.append(i)
            labels.append(f"Model {i}")
            
            # Visual vertical boundary line
            ax1.axvline(i - 0.5, color='gray', linestyle='--', alpha=0.5)
            
        # Final explicit right boundary
        ticks.append(num_models - 0.5)
        labels.append(f"{num_models - 0.5}")
        ax1.axvline(num_models - 0.5, color='gray', linestyle='--', alpha=0.5)
        
        ax1.set_xticks(ticks)
        ax1.set_xticklabels(labels, rotation=45 if num_models > 4 else 0)
        if num_models <= 10:
            ax1.legend(loc="upper right", prop={'size': 8})
        ax1.set_ylabel("Continuous Density")
        st.pyplot(fig1)

    with plot_col2:
        fig2, ax2 = plt.subplots(figsize=(4, 3))
        
        # Discretize predictions aggressively using mathematical snapping rounds
        preds_list = [np.round(s).astype(int).clip(0, num_models - 1) for s in model_samples]
        bins = np.arange(-0.5, num_models + 0.5, 1)
        
        # Determine explicit coloring mapping mirroring KDE
        hist_colors = [colors[c_idx % len(colors)] for c_idx in indices_to_show]
        weights_list = [np.ones_like(p) / len(p) * 100 for p in preds_list]
        
        ax2.hist(
            preds_list, 
            bins=bins, 
            weights=weights_list,
            color=hist_colors, 
            label=[f"True {c_idx}" for c_idx in indices_to_show], 
            align='mid'
        )
        ax2.set_title("Predicted Discrete State Histogram")
        ax2.set_ylabel("Percentage (%)")
        ax2.set_xticks(range(num_models))
        ax2.set_xticklabels([str(i) for i in range(num_models)])
        ax2.set_xlim(-0.5, num_models - 0.5)
        if num_models <= 10:
            ax2.legend(loc="upper right", prop={'size': 8})
        st.pyplot(fig2)

if __name__ == "__main__":
    st.set_page_config(page_title="Ill-Posedness Conformations", layout="wide")
    render_ui()
