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
        
    # 2. Dynamic Images Row (Choose Models for Slot A and Slot B)
    indices_to_show = []
    images_noisy_list = []
    slot_labels = ["A", "B"]
    cols = st.columns(len(slot_labels))
    
    for i, (col, label) in enumerate(zip(cols, slot_labels)):
        with col:
            default_val = 0 if i == 0 else (num_models - 1 if num_models > 1 else 0)
            c_idx = st.slider(f"Select Model for Slot {label}", 0, num_models - 1, default_val, key=f"idx_{label}")
            indices_to_show.append(c_idx)
            
            st.write(f"**Slot {label}: Model {c_idx}**")
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
            plt.close(fig)
            
    st.divider()
    
    # Redo-sampling button to regenerate noise and re-evaluate posterior
    btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
    with btn_col2:
        st.button("Redo Sampling (Generate New Noise & Infer)", width="stretch")
    
    # 3. Dynamic Inference Block
    if posterior is None:
        st.info("No valid `estimator.pt` or `training_parameters.json` found in this model directory! Train an SBI Neural Flow to unlock posterior inference plotting.")
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
        
        # Calculate Posterior Statistics
        preds_list = [np.round(s).astype(int).clip(0, num_models - 1) for s in model_samples]
        
        stats = []
        for i in range(num_inferences):
            s = model_samples[i]
            p = preds_list[i]
            # Mode (Top Index)
            counts = np.bincount(p, minlength=num_models)
            top_idx = int(np.argmax(counts))
            # Mean and Std
            mean_val = float(np.mean(s))
            std_val = float(np.std(s))
            stats.append({"top": top_idx, "mean": mean_val, "std": std_val})
            
    # Visual Layout - Centered Posterior Plot
    _, center_col, _ = st.columns([1, 8, 1])
    
    with center_col:
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        
        # Iterate dynamic KDEs matching each evaluated base
        colors = plt.cm.tab10.colors
        for i, c_idx in enumerate(indices_to_show):
            c = colors[c_idx % len(colors)]
            label = slot_labels[i]
            sns.kdeplot(model_samples[i], ax=ax1, fill=True, color=c, label=f"Slot {label} Posterior (True Model {c_idx})", warn_singular=False)
            
            # Highlight target bin
            ax1.axvspan(c_idx - 0.5, c_idx + 0.5, color=c, alpha=0.1, label=f"Slot {label} Ideal Range")

            # Add mean and std error bars at y=0.1
            mean_val = stats[i]["mean"]
            std_val = stats[i]["std"]
            ax1.errorbar(mean_val, 0.1, xerr=std_val, fmt='|', color=c, capsize=3, elinewidth=2, markeredgewidth=2, label=f"Slot {label} Estimator Mean ± Std")
            
        ax1.set_title("Continuous Posterior Density")
        ax1.set_xlim(-0.5, num_models - 0.5)
        
        # Dynamically build ticks at both the integer centers and fractional boundaries
        ticks = []
        labels = []
        for i in range(num_models):
            # Left boundary (tick but no label)
            ticks.append(i - 0.5)
            labels.append("")
            
            # Center integer (model identifier)
            ticks.append(i)
            labels.append(f"Model {i}")
            
            # Visual vertical boundary line
            ax1.axvline(i - 0.5, color='gray', linestyle='--', alpha=0.5)
            
        # Final explicit right boundary (tick but no label)
        ticks.append(num_models - 0.5)
        labels.append("")
        ax1.axvline(num_models - 0.5, color='gray', linestyle='--', alpha=0.5)
        
        ax1.set_xticks(ticks)
        ax1.set_xticklabels(labels, rotation=45 if num_models > 4 else 0)
        if num_models <= 10:
            ax1.legend(loc="upper right", prop={'size': 8})
        st.pyplot(fig1)
        plt.close(fig1)

    # 4. Explanatory Expanders
    with st.expander("How to read the Posterior"):
        st.markdown(r"""
            **Continuous Posterior Density (KDE):** This plot shows the continuous probability distribution over the model index. Since our method learns an approximate neural posterior $q(\theta | x)$,
            we can draw many samples from this posterior (typically around 2000). From these samples, we estimate a smooth posterior density using Kernel Density Estimation (KDE): conceptually, KDE places many small bell curves (otherwise known as _Gaussian kernels_) at the sampled values and adds them up, such that we receive a smooth approximation of the neural posterior estimate.
            During training, the conformation index is sampled from a **continuous uniform distribution** over the entire range of models.
            When generating a new training set ($\theta, x_{obs}$) one sample from the priors and gets, for example, $\theta = 0.4434$. For the generation of the final image ths is then rounded to Model 0 before performing the simulation pass.
            
            - **Ideal Range Highlight:** Due to this training scheme, a perfectly calibrated model should produce a **uniform distribution** 
              filling the entire parameter space where it $\theta$ is rounded to the correct model index, here represented by the shaded box. Note: We are not sure why the estimator seems to struggle with the very boundaries of possible conformational indices.
            - **Estimator Mean ± Std:** The vertical marker and error bars represent the model's quantitative estimate.
        """)
        
    with st.expander("Interesting things to try"):
        st.markdown("""
            Here are some key insights to explore in this widget:
            
            1. **Conformational Confidence Changes:** Compare 'early' (low index) vs 'late' (high index) conformationalal changes. If you don't remember how the cat animation looks, scroll up a bit ;) 
               You may notice the model is more certain for earlier indices. This is probably due to the fact that the underlying conformational differences become more subtle 
                and thus the model's uncertainty increases. This results in producing broader, flatter distributions.
            
            2. **The "Angle" of Ambiguity:** Try rotating the models so they are viewed from the top or bottom. 
               When features like the feet and tail become less visible, even models trained on vast datasets struggle to 
               distinguish between similar conformations. We often, depending on the noise, get very ambigous results for rotations of (0°,180°,~310°).
            
            3. **Learning from Noise:** Despite the images often looking like pure static to our eyes due to high noise and 
               CTF effects, the model still extracts structural features that allow it to perform inference. We think that's pretty amazing.
        """)

if __name__ == "__main__":
    st.set_page_config(page_title="Ill-Posedness Conformations", layout="wide")
    render_ui()
