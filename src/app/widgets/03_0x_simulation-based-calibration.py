import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

# ==========================================
# Fragment 1: Single Trial Visualization
# ==========================================
@st.fragment
def render_single_trial():
    st.subheader("1. The Anatomy of a Single Trial")
    st.write("In SBC, we compute how often the True $\\theta^*$ falls below the samples drawn from the Predicted Posterior.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        true_theta = st.slider("True $\\theta^*$", -5.0, 5.0, 0.0, 0.1, key="sbc_1_theta")
    with col2:
        post_mu = st.slider("Predicted Posterior Mean $\\mu$", -5.0, 5.0, 0.0, 0.1, key="sbc_1_mu")
    with col3:
        post_sigma = st.slider("Predicted Posterior StdDev $\\sigma$", 0.1, 3.0, 1.0, 0.1, key="sbc_1_sigma")
    
    M = st.slider("Number of Posterior Samples $M$", 10, 100, 20, 1, key="sbc_1_m")
    
    # 1. Math
    # Draw M samples from the predicted posterior N(mu, sigma^2)
    samples = np.random.normal(post_mu, post_sigma, M)
    
    # Compute rank
    rank = np.sum(samples < true_theta)
    
    # 2. Plot
    fig, ax = plt.subplots(figsize=(10, 3))
    
    # Plot posterior Gaussian curve
    x_min = min(true_theta, post_mu) - 4*post_sigma
    x_max = max(true_theta, post_mu) + 4*post_sigma
    x = np.linspace(x_min, x_max, 500)
    y = stats.norm.pdf(x, post_mu, post_sigma)
    
    ax.plot(x, y, color='blue', label='Predicted Posterior $Q(\\theta)$')
    ax.fill_between(x, 0, y, color='blue', alpha=0.1)
    
    # Plot samples
    ax.scatter(samples, np.zeros_like(samples), color='blue', marker='|', s=200, label=f'{M} Samples $\\tilde{{\\theta}}$', zorder=3)
    
    # Plot True Theta
    ax.axvline(true_theta, color='red', linestyle='--', linewidth=2, label='True $\\theta^*$', zorder=4)
    
    ax.set_ylim(-0.05 * np.max(y), np.max(y) * 1.2)
    ax.set_yticks([])
    ax.set_xlabel("$\\theta$ value")
    ax.legend(loc='upper right')
    
    st.pyplot(fig)
    
    st.info(f"**Rank Result:** Out of {M} samples, exactly **{rank}** were less than the True $\\theta^*$. \n\n Therefore, the rank for this trial is **{rank}**.")
    st.markdown("---")


# ==========================================
# Fragment 2: Mass Trial / LLN SBC Histogram
# ==========================================
@st.fragment
def render_sbc_mass_trials():
    st.subheader("2. The Law of Large Numbers (SBC Rank Histogram)")
    st.write("If the model is perfectly calibrated, doing the above trial $N$ times with mathematically correct posteriors will result in a perfectly flat histogram of ranks. Let's manually introduce model pathologies and see how the geometric histogram breaks.")
    
    col1, col2 = st.columns(2)
    with col1:
        bias = st.slider("Systematic Bias (Prediction offset)", -2.0, 2.0, 0.0, 0.1, key="sbc_2_bias")
    with col2:
        dispersion = st.slider("Dispersion Factor (Prediction width)", 0.2, 3.0, 1.0, 0.1, key="sbc_2_disp")
        
    N = 2000
    M = 50
    st.write(f"*(Simulating mathematically $N={N}$ independent trials with $M={M}$ samples per trial...)*")
    
    # Vectorized SBC simulation
    
    # To simulate N mathematically perfectly calibrated trials without needing full Bayesian likelihood updates:
    # 1. Define physical target posterior means randomly across the space
    ideal_mus = np.random.normal(0, 2.0, N)
    
    # 2. Draw the TRUE theta for each trial directly out of the ideal, perfectly calibrated posterior N(ideal_mu, 1)
    true_thetas = np.random.normal(ideal_mus, 1.0)
    
    # 3. Apply the user's pathology (Prediction Bias and Dispersion width) to the ideal posterior
    predicted_mus = ideal_mus + bias
    predicted_sigmas = np.ones(N) * dispersion
    
    # 4. Draw M samples from the user's *predicted* posterior
    # Shape: (N, M)
    samples = np.random.normal(predicted_mus[:, None], predicted_sigmas[:, None], (N, M))
    
    # 4. Compute rank for each trial
    # Compare (N, M) to (N, 1) -> sums across columns
    ranks = np.sum(samples < true_thetas[:, None], axis=1)
    
    # 5. Plot
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Bins from exactly -0.5 to M+0.5 so each integer 0..M lands perfectly in the center of a bar
    bins = np.arange(-0.5, M + 1.5, 1)
    counts, _, _ = ax.hist(ranks, bins=bins, color='purple', edgecolor='black', alpha=0.7, density=True)
    
    # Expected uniform height = 1 / (M + 1)
    expected_height = 1.0 / (M + 1)
    ax.axhline(expected_height, color='black', linestyle='--', linewidth=2, label='Perfect Calibration (Uniform)')
    
    # Force Y-axis scale to be somewhat locked so optical illusions don't mess with perception
    # We allow it to scale up if U-shape breaks constraints, but keep minimum height.
    max_count = np.max(counts)
    ax.set_ylim(0, max(expected_height * 2.5, max_count * 1.1))
    
    ax.set_xlim(-1, M + 1)
    ax.set_xlabel(f"Rank (0 to {M})")
    ax.set_ylabel("Relative Frequency")
    ax.legend(loc='upper center')
    
    st.pyplot(fig)
    
    # Auto-analysis readout
    if bias > 0.5:
        st.warning("Notice the slope! A positive bias causes the model to consistently guess too high, pushing the True $\\theta^*$ into the lowest ranks.")
    elif bias < -0.5:
        st.warning("Notice the slope! A negative bias causes the model to consistently guess too low, pushing the True $\\theta^*$ into the highest ranks.")
    elif dispersion < 0.7:
        st.error("Notice the U-shape! The model is **overconfident** (too narrow). The True $\\theta^*$ frequently lands completely outside the tight predictions, piling up at ranks 0 and M.")
    elif dispersion > 1.5:
        st.info("Notice the Bathtub (∩) shape! The model is **underconfident** (too wide). The predicted posterior stretches so wide that the True $\\theta^*$ always safely lands near the middle, starving the 0 and M rank edges.")
    else:
        st.success("Perfectly Uniform! The model predicts exactly the correct data distribution without bias or over/under-confidence.")


def render():
    st.markdown("## Interactive SBC Visualizer")
    st.write("Simulation-Based Calibration provides a geometric sanity check: if our neural network genuinely learned the correct posterior distribution $p(\\theta | x)$, then the true parameter $\\theta^*$ behind any simulated observation $x$ must look like a perfectly ordinary drawn sample from that predicted posterior.")
    
    render_single_trial()
    render_sbc_mass_trials()


if __name__ == "__main__":
    st.set_page_config(page_title="SBC Intuition", layout="centered")
    render()
