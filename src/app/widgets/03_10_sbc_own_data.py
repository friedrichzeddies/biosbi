import streamlit as st
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from scipy.spatial.transform import Rotation as R

# Internal cryo_sbi imports
from cryo_sbi.wpa_simulator.cryo_em_simulator import cryo_em_simulator, CryoEmSimulator
import cryo_sbi.utils.estimator_utils as est_utils

# ==========================================
# Resource Caching
# ==========================================

@st.cache_resource
def load_assets(model_dir):
    """Caches the simulator and estimator for a given model directory."""
    sim_json = os.path.join(model_dir, "simulation_parameters.json")
    train_json = os.path.join(model_dir, "training_parameters.json")
    estimator_pt = os.path.join(model_dir, "estimator.pt")
    
    if not os.path.exists(sim_json):
        return None, None
        
    simulator = CryoEmSimulator(sim_json, device="cpu")
    
    posterior = None
    if os.path.exists(train_json) and os.path.exists(estimator_pt):
        try:
            posterior = est_utils.load_estimator(train_json, estimator_pt, device="cpu")
        except Exception as e:
            st.error(f"Failed to load estimator: {e}")
            
    return simulator, posterior

# ==========================================
# Fragment 1: Single Trial Sandbox
# ==========================================

@st.fragment
def _render_single_trial(simulator, posterior, M):
    st.markdown("### 1. Single Trial Sandbox")
    st.write("Draw a single ground-truth conformation from the prior, simulate its 2D projection, and ask the model to guess the posterior.")
    
    if st.button("🚀 Simulate New Trial", key="sbc_own_sim_btn"):
        # 1. Sample True Theta* and Nuisance params from PRIOR
        parameters = simulator._priors.sample((1,))
        true_idx = parameters[0][0, 0].item()
        
        # 2. Simulate Image x
        with st.spinner("Simulating..."):
            image = cryo_em_simulator(
                simulator._models,
                *parameters,
                simulator._num_pixels,
                simulator._pixel_size
            )
        
        # 3. Draw Posterior Samples (High Fidelity for KDE + M for SBC rank)
        if posterior is not None:
            with st.spinner("Sampling Posterior..."):
                # Full posterior for the KDE
                full_samples = est_utils.sample_posterior(
                    estimator=posterior, images=image, 
                    num_samples=1000, batch_size=1000, device="cpu"
                )
                # Subset for SBC rank calculation (the "M" samples)
                # sample_posterior returns (num_samples, batch)
                sbc_samples = full_samples[:M, 0].detach().numpy()
                full_kde_samples = full_samples[:, 0].detach().numpy()
                
                # Calculate Rank
                rank = np.sum(sbc_samples < true_idx)
                
                # Visualization
                vis_col1, vis_col2 = st.columns([1, 2])
                
                with vis_col1:
                    st.write(f"**Simulated Image** ($\theta^* = {true_idx:.2f}$)")
                    fig1, ax1 = plt.subplots(figsize=(4, 4))
                    ax1.imshow(image[0].numpy(), cmap='gray')
                    ax1.axis('off')
                    st.pyplot(fig1)
                    
                with vis_col2:
                    st.write(f"**Inferred Posterior** (Rank: {rank})")
                    # Full visualization: KDE + Discrete Histogram
                    fig2, (ax_kde, ax_hist) = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={'width_ratios': [2, 1]})
                    
                    num_models = len(simulator._models)
                    
                    # --- 1. KDE Plot (Continuous) ---
                    sns.kdeplot(full_kde_samples, ax=ax_kde, fill=True, color='purple', label="Model Belief (KDE)")
                    ax_kde.plot(sbc_samples, np.zeros_like(sbc_samples), 'b|', markersize=10, alpha=0.5, label=f"SBC Samples ($M={M}$)")
                    ax_kde.axvline(true_idx, color='red', linewidth=2, label=f"True $\\theta^*$ ({true_idx:.2f})")
                    
                    # De-Quantization Boundaries (Skill #6)
                    ticks = []
                    labels = []
                    for i in range(num_models):
                        ax_kde.axvline(i - 0.5, color='gray', linestyle='--', alpha=0.3)
                        ticks.append(i)
                        labels.append(f"Model {i}")
                    ax_kde.axvline(num_models - 0.5, color='gray', linestyle='--', alpha=0.3)
                    
                    ax_kde.set_xlim(-0.5, num_models - 0.5)
                    ax_kde.set_xticks(ticks)
                    ax_kde.set_xticklabels(labels, rotation=45 if num_models > 4 else 0)
                    ax_kde.set_ylabel("Continuous Density")
                    ax_kde.legend(loc='upper right', prop={'size': 7})
                    
                    # --- 2. Discrete Histogram (Skill #6) ---
                    preds = np.round(full_kde_samples).astype(int).clip(0, num_models - 1)
                    weights = np.ones_like(preds) / len(preds) * 100
                    ax_hist.hist(preds, bins=np.arange(-0.5, num_models + 0.5, 1), weights=weights, color='purple', alpha=0.5, edgecolor='black')
                    ax_hist.set_title("Discrete Probability")
                    ax_hist.set_ylabel("Percentage (%)")
                    ax_hist.set_xticks(range(num_models))
                    ax_hist.set_xticklabels([str(i) for i in range(num_models)])
                    ax_hist.set_xlim(-0.5, num_models - 0.5)
                    
                    plt.tight_layout()
                    st.pyplot(fig2)
                
                st.info(f"**Calculated Rank:** The true $\\theta^*$ ({true_idx:.2f}) is larger than **{rank}** out of the {M} samples.")
                st.markdown("""
                    > **💡 Why two types of samples?**  
                    > To get that smooth purple KDE curve, we have to sample the posterior **many hundreds of times** (e.g., 1000+). This is great for visualizing a single result, but it's too slow for a mass validation of 2000 trials. 
                    > 
                    > For **SBC**, we only need a few samples (the **blue marks** on the axis) to calculate a valid rank statistic. In the mass validation below, we use this faster approach to check the model's overall honesty.
                """)
        else:
            st.warning("No estimator loaded. Plotting simulated image only.")
            fig1, ax1 = plt.subplots(figsize=(4, 4))
            ax1.imshow(image[0].numpy(), cmap='gray')
            ax1.axis('off')
            st.pyplot(fig1)

# ==========================================
# Fragment 2: Mass SBC Validation
# ==========================================

@st.fragment
def _render_mass_sbc(simulator, posterior, M):
    st.markdown("### 2. Mass Trial Validation")
    st.write("Perform $N$ trials to check if the model is statistically well-calibrated across your priors.")
    
    col_n, col_run = st.columns([1, 1])
    with col_n:
        N = st.number_input("Number of Trials $N$", 50, 2000, 200, 50, key="sbc_own_n")
    
    if st.button("📊 Run Mass SBC Comparison", key="sbc_own_mass_run"):
        if posterior is None:
            st.error("Cannot run SBC without a trained estimator!")
            return
            
        ranks = []
        progress_bar = st.progress(0)
        
        # Run in batches for efficiency if N is large
        batch_size = 50
        num_batches = int(np.ceil(N / batch_size))
        
        for b in range(num_batches):
            current_batch_size = min(batch_size, N - len(ranks))
            
            # 1. Sample Params
            params = simulator._priors.sample((current_batch_size,))
            true_indices = params[0][:, 0]
            
            # 2. Simulate Images
            images = cryo_em_simulator(
                simulator._models,
                *params,
                simulator._num_pixels,
                simulator._pixel_size
            )
            
            # 3. Batch Infer Posterior
            samples = est_utils.sample_posterior(
                estimator=posterior, images=images,
                num_samples=M, batch_size=M, device="cpu"
            )
            
            # 4. Calculate Ranks
            # samples shape: [M, current_batch_size]
            samples_2d = samples.detach().numpy() 
            true_vals = true_indices.detach().numpy()
            
            for i in range(current_batch_size):
                # We need samples_2d[:, i]
                r = np.sum(samples_2d[:, i] < true_vals[i])
                ranks.append(r)
            
            progress_bar.progress((len(ranks)) / N)
            
        ranks = np.array(ranks)
        
        # Plotting
        fig_res, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # 1. Rank Histogram
        bins = np.arange(-0.5, M + 1.5, 1)
        ax1.hist(ranks, bins=bins, color='purple', alpha=0.7, density=True, edgecolor='white')
        p = 1.0 / (M + 1)
        ax1.axhline(p, color='black', linestyle='--', linewidth=1.5, label='Perfect Calibration')
        # 95% Binomial CI
        ci = 1.96 * np.sqrt(p * (1 - p) / N)
        ax1.fill_between([-1, M + 1], p - ci, p + ci, color='gray', alpha=0.2, label='95% CI')
        ax1.set_title("Rank Histogram")
        ax1.set_xlabel(f"Rank (0 to {M})")
        ax1.set_xlim(-0.5, M + 0.5)
        ax1.legend()
        
        # 2. ECDF
        sorted_ranks = np.sort(ranks)
        ecdf_y = np.arange(1, N + 1) / N
        diag_x = np.linspace(0, M, 300)
        diag_y = (diag_x + 1) / (M + 1)
        # 95% CI (DKW) -> using simple shaded band for intuition
        epsilon = np.sqrt(np.log(2.0 / 0.05) / (2 * N))
        ax2.fill_between(diag_x, np.clip(diag_y - epsilon, 0, 1), np.clip(diag_y + epsilon, 0, 1), 
                         color='lightblue', alpha=0.5, label='95% CI')
        ax2.step(sorted_ranks, ecdf_y, where='post', color='purple', linewidth=2, label='Observed ECDF')
        ax2.set_title("ECDF Plot")
        ax2.set_xlabel(f"Rank (0 to {M})")
        ax2.set_ylim(0, 1.02)
        ax2.legend()
        
        st.pyplot(fig_res)
        
        # 3. Dynamic Pathology Explainers
        # Using independent flags so multiple issues can be reported
        has_pathology = False
        
        # Check for Overconfidence (U-shape)
        # In a U-shape, variance of ranks is higher than Expected (Uniform Variance)
        observed_std = np.std(ranks)
        expected_std = np.sqrt(((M + 1)**2 - 1) / 12)
        
        if observed_std > expected_std * 1.1:
            st.error("🚨 **Pathology: Overconfident Model (U-Shape)**")
            st.write("The model's posterior is too narrow. The true parameter frequently lands outside the predicted range, causing ranks to pile up at the extreme 0 and $M$ edges.")
            has_pathology = True
        elif observed_std < expected_std * 0.9:
            st.info("ℹ️ **Pathology: Underconfident Model (Bathtub ∩)**")
            st.write("The model's posterior is too wide. The true parameter almost always lands safely in the middle, leaving the edges of the rank histogram empty.")
            has_pathology = True
            
        # Check for Systematic Bias (Skew)
        avg_rank = np.mean(ranks)
        exp_rank = M / 2.0
        # Standard error of the mean for uniform: sqrt(Var/N)
        sem = expected_std / np.sqrt(N)
        
        if avg_rank > exp_rank + (3.0 * sem):
            st.warning("⚠️ **Pathology: Underestimation Bias**")
            st.write("On average, the model predicts indices that are **smaller** than the truth (pushing the true $\\theta^*$ to a higher rank).")
            has_pathology = True
        elif avg_rank < exp_rank - (3.0 * sem):
            st.warning("⚠️ **Pathology: Overestimation Bias**")
            st.write("On average, the model predicts indices that are **larger** than the truth (pushing the true $\\theta^*$ to a lower rank).")
            has_pathology = True
            
        if not has_pathology:
            st.success("✅ **Calibration Success!** The model appears statistically honest. The ranks are approximately uniform, meaning the model's uncertainty matches the actual error rate.")

# ==========================================
# Main App
# ==========================================

def render():
    st.markdown("## 🔍 Internal Validation: SBC on Your Data")
    st.write("""
        Now we apply the Simulation-Based Calibration (SBC) framework to your real cat conformations. 
        Select a model below to check if its posterior estimates are well-calibrated.
    """)
    
    # 1. Model Selection
    models_base_dir = "src/app/data/models"
    if not os.path.exists(models_base_dir):
        st.error("Models directory not found!")
        return
        
    available_models = sorted([d for d in os.listdir(models_base_dir) if os.path.isdir(os.path.join(models_base_dir, d))])
    selected_model_name = st.selectbox("Select Model to Validate", available_models)
    model_dir = os.path.join(models_base_dir, selected_model_name)
    
    # 2. Shared Config
    M = st.slider("Number of Predicted Samples $M$ for SBC", 10, 100, 40, 5, help="How many samples to use for calculating the rank in each trial.")
    
    # 3. Load Assets
    simulator, posterior = load_assets(model_dir)
    
    if simulator is None:
        st.error(f"Could not load simulator for {selected_model_name}.")
        return

    # 4. Render Fragments
    _render_single_trial(simulator, posterior, M)
    st.divider()
    _render_mass_sbc(simulator, posterior, M)

if __name__ == "__main__":
    st.set_page_config(page_title="SBC Own Data", layout="centered")
    render()
