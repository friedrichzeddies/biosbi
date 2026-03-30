import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

def _apply_preset():
    preset = st.session_state.sbc_preset
    
    # Range boundaries for clamping (must match st.slider calls below)
    MU_MIN, MU_MAX = -4.0, 4.0
    SIG_MIN, SIG_MAX = 0.1, 3.0

    target_mu = st.session_state.get("sbc_1_mu", 0.0)
    target_sig = st.session_state.get("sbc_1_sigma", 1.0)

    if preset == "Exact Match":
        target_mu = 0.0
        target_sig = 1.0
    elif preset == "Model Too Certain":
        target_mu = 0.0
        target_sig = 0.2
    elif preset == "Model Too Uncertain":
        target_mu = 0.0
        target_sig = 3.0
    elif preset == "Model Overestimating":
        target_mu = 1.5
        target_sig = 1.0
    elif preset == "Model Underestimating":
        target_mu = -1.5
        target_sig = 1.0
    
    # Apply clamped values to session state
    if preset != "Manual":
        st.session_state.sbc_1_mu = float(np.clip(target_mu, MU_MIN, MU_MAX))
        st.session_state.sbc_1_sigma = float(np.clip(target_sig, SIG_MIN, SIG_MAX))

def _make_manual():
    st.session_state.sbc_preset = "Manual"

@st.fragment
def _render_single_trial(post_mu, post_sigma, M):
    """Isolated fragment: button only re-runs this panel."""
    st.subheader("1. Single Trial Anatomy")

    # Initialize true theta state
    if "sbc_1_true_theta" not in st.session_state:
        st.session_state.sbc_1_true_theta = float(np.random.normal(0, 1.0))

    if st.button("Simulate New Trial (Draw True $\\theta^*$ & Re-sample)", help="Randomly draws a new true parameter from the Prior, and redraws the simulated posterior samples.", width="stretch"):
        st.session_state.sbc_1_true_theta = float(np.random.normal(0, 1.0))

    true_theta = st.session_state.sbc_1_true_theta
    st.markdown(f"**Current True $\\theta^*$**: `{true_theta:+.3f}`")

    # Draw M samples from the predicted posterior N(mu, sigma^2)
    samples = np.random.normal(post_mu, post_sigma, M)

    # Compute rank
    rank = np.sum(samples < true_theta)

    # Single Trial Plot
    fig1, ax1 = plt.subplots(figsize=(6, 4))

    # Plot True Posterior N(0, 1) as a dashed red line
    true_post_x = np.linspace(-4, 4, 300)
    true_post_y = stats.norm.pdf(true_post_x, 0, 1.0)
    ax1.plot(true_post_x, true_post_y, color='red', linestyle='--', alpha=0.7, label='True Posterior $P^*(\\theta)$')
    ax1.fill_between(true_post_x, 0, true_post_y, color='red', alpha=0.05)

    # Plot dynamic predicted posterior Gaussian curve
    x_min = min(true_theta, post_mu) - 4*post_sigma
    x_max = max(true_theta, post_mu) + 4*post_sigma
    x = np.linspace(x_min, x_max, 500)
    y = stats.norm.pdf(x, post_mu, post_sigma)

    ax1.plot(x, y, color='blue', label='Predicted Posterior $Q(\\theta|x)$')
    ax1.fill_between(x, 0, y, color='blue', alpha=0.15)

    # Plot samples as blue rug ticks
    ax1.scatter(samples, np.zeros_like(samples), color='blue', marker='|', s=200, label=f'{M} Samples $\\tilde{{\\theta}}$', zorder=3)

    # Plot True Theta as a slightly larger red rug tick (legend omitted — red dashed curve already identifies it)
    ax1.scatter([true_theta], [0], color='red', marker='|', s=400, linewidths=2, label='_nolegend_', zorder=4)

    # Lock axes
    ax1.set_xlim(-8, 8)
    global_max_y = max(np.max(y), np.max(true_post_y))
    ax1.set_ylim(-0.05 * global_max_y, global_max_y * 1.2)
    ax1.set_yticks([])
    ax1.set_xlabel("$\\theta$ value")
    ax1.legend(loc='upper right')

    st.pyplot(fig1, clear_figure=True)
    plt.close(fig1)
    
    # Small explainer box for this specific trial's rank
    with st.container(height=120, border=False):
        st.info(f"**Rank of $\\theta^*$ = {rank}** — Out of {M} predicted posterior samples, **{rank}** fell below the true $\\theta^*={true_theta:+.2f}$. That places $\\theta^*$ at position {rank} out of {M}.")
@st.fragment
def _render_histogram(post_mu, post_sigma, M):
    """Isolated fragment: only re-runs when sliders change, NOT when the trial button is pressed."""
    st.subheader("2. LLN SBC Histogram")

    N = 2000
    st.write(f"*(Simulating $N={N}$ trials: each draws True $\\theta^*$ from $P^*(\\theta)=\\mathcal{{N}}(0,1)$ and {M} samples from $Q(\\theta)=\\mathcal{{N}}({post_mu:.1f},\\,{post_sigma:.1f})$...)*")

    # Vectorized SBC simulation — directly mirrors the Single Trial panel:
    # 1. Draw N true thetas from the True Posterior N(0, 1) (the red dashed curve)
    true_thetas = np.random.normal(0, 1.0, N)

    # 2. Draw M samples from the Predicted Posterior N(post_mu, post_sigma) for each trial
    # Shape: (N, M)
    mass_samples = np.random.normal(post_mu, post_sigma, (N, M))

    # 3. Compute rank for each trial
    ranks = np.sum(mass_samples < true_thetas[:, None], axis=1)

    # Plot
    fig2, ax2 = plt.subplots(figsize=(6, 4))

    bins = np.arange(-0.5, M + 1.5, 1)
    counts, _, _ = ax2.hist(ranks, bins=bins, color='purple', edgecolor='black', alpha=0.7, density=True)

    # Expected uniform height p = 1 / (M + 1)
    p = 1.0 / (M + 1)
    ax2.axhline(p, color='black', linestyle='--', linewidth=2, label='Perfect Calibration (Uniform)')

    # 95% Binomial CI band
    ci_margin = 1.96 * np.sqrt(p * (1 - p) / N)
    ax2.fill_between([-1, M + 1], p - ci_margin, p + ci_margin, color='gray', alpha=0.3, label='95% CI Band')

    max_count = np.max(counts)
    ax2.set_ylim(0, max(p * 2.5, max_count * 1.1))
    ax2.set_xlim(-1, M + 1)
    ax2.set_xlabel(f"Rank of $\\theta^*$ (0 to {M})")
    ax2.set_ylabel("Relative Frequency")
    ax2.legend(loc='upper center')

    st.pyplot(fig2, clear_figure=True)
    plt.close(fig2)

    # Auto-analysis readout (independent checks so both mean and width pathologies can fire simultaneously)
    with st.container(height=280, border=False):
        has_pathology = False
        if post_mu > 0.5:
            st.warning("**Mean shift →** The histogram slopes downward! The predicted posterior mean is shifted **right** of the true posterior, pushing ranks low.")
            has_pathology = True
        if post_mu < -0.5:
            st.warning("**Mean shift ←** The histogram slopes upward! The predicted posterior mean is shifted **left** of the true posterior, pushing ranks high.")
            has_pathology = True
        if post_sigma < 0.7:
            st.error("**Width too narrow →** U-shape! The model is **overconfident**. The True $\\theta^*$ frequently lands completely outside the tight predictions, piling up at ranks 0 and $M$.")
            has_pathology = True
        if post_sigma > 1.5:
            st.info("**Width too wide →** Bathtub (∩) shape! The model is **underconfident**. The predicted posterior stretches so wide that the True $\\theta^*$ always safely lands near the middle, starving the 0 and $M$ rank edges.")
            has_pathology = True
        if not has_pathology:
            st.success("Perfectly Uniform! The model predicts exactly the correct data distribution without bias or over/under-confidence.")


def render():
    # Shared controls (outside fragments — changing these re-runs the whole page, updating both panels)
    presets = ["Manual", "Exact Match", "Model Too Certain", "Model Too Uncertain", "Model Overestimating", "Model Underestimating"]
    st.selectbox("Quick Presets", presets, key="sbc_preset", on_change=_apply_preset)

    col1, col2 = st.columns(2)
    with col1:
        post_mu = st.slider("Predicted Posterior Mean $\\mu$", -4.0, 4.0, 0.0, 0.1, key="sbc_1_mu", on_change=_make_manual)
    with col2:
        post_sigma = st.slider("Predicted Posterior StdDev $\\sigma$", 0.1, 3.0, 1.0, 0.1, key="sbc_1_sigma", on_change=_make_manual)

    M = st.slider("Number of Predicted Posterior Samples $M$", 10, 100, 20, 1, key="sbc_1_m", on_change=_make_manual)

    # Side-by-side fragments — each re-runs independently
    vis_col1, vis_col2 = st.columns(2)
    with vis_col1:
        _render_single_trial(post_mu, post_sigma, M)
    with vis_col2:
        _render_histogram(post_mu, post_sigma, M)
    
    # ==========================================
    # Sidequest: Why ECDF over Histogram?
    # ==========================================
    with st.expander("Sidequest: Is a histogram the best choice?"):
        # ECDF plot at the top of the expander
        N_ecdf = 2000
        true_thetas_ecdf = np.random.normal(0, 1.0, N_ecdf)
        mass_samples_ecdf = np.random.normal(post_mu, post_sigma, (N_ecdf, M))
        ranks_ecdf = np.sum(mass_samples_ecdf < true_thetas_ecdf[:, None], axis=1)
        
        sorted_ranks = np.sort(ranks_ecdf)
        ecdf_y = np.arange(1, N_ecdf + 1) / N_ecdf
        
        # DKW 95% confidence band
        alpha = 0.05
        epsilon = np.sqrt(np.log(2.0 / alpha) / (2 * N_ecdf))
        
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        
        # 95% CI band (min/max envelope around the uniform CDF diagonal)
        diag_x = np.linspace(0, M, 300)
        diag_y = (diag_x + 1) / (M + 1)
        ax3.fill_between(diag_x, np.clip(diag_y - epsilon, 0, 1), np.clip(diag_y + epsilon, 0, 1),
                         color='lightblue', alpha=0.5, label='95% CI')
        
        # ECDF staircase
        ax3.step(sorted_ranks, ecdf_y, where='post', color='purple', linewidth=2, label='Observed ECDF')
        
        ax3.set_xlim(-0.5, M + 0.5)
        ax3.set_ylim(0, 1.02)
        ax3.set_xlabel(f"Rank of $\\theta^*$ (0 to {M})")
        ax3.set_ylabel("Cumulative Probability")
        ax3.legend(loc='upper left')
        ax3.set_title("ECDF of SBC Ranks")
        
        st.pyplot(fig3, clear_figure=True)
        plt.close(fig3)
        
        # Auto-analysis readout for ECDF (independent checks)
        with st.container(height=280, border=False):
            has_ecdf_pathology = False
            if post_mu > 0.5:
                st.warning("**Mean shift →** The ECDF **bows above** the band — the predicted posterior is shifted **right**, so ranks pile up low and the cumulative curve rises too fast on the left.")
                has_ecdf_pathology = True
            if post_mu < -0.5:
                st.warning("**Mean shift ←** The ECDF **bows below** the band — the predicted posterior is shifted **left**, so ranks pile up high and the cumulative curve lags behind.")
                has_ecdf_pathology = True
            if post_sigma < 0.7:
                st.error("**Width too narrow →** The ECDF forms an **S-shape** crossing through the band — the model is **overconfident**. Ranks cluster at the extremes (0 and $M$), causing the curve to rise steeply at both ends.")
                has_ecdf_pathology = True
            if post_sigma > 1.5:
                st.info("**Width too wide →** The ECDF stays **flat at the edges** and rises steeply in the middle — the model is **underconfident**. The True $\\theta^*$ almost always lands in the center of the over-wide posterior, starving the extreme ranks.")
                has_ecdf_pathology = True
            if not has_ecdf_pathology:
                st.success("The ECDF tracks perfectly inside the 95% CI band — the model is well-calibrated!")
        
        st.markdown("""
The rank histogram is probably the simplest SBC visualization — but it has one key **disadvantage**: **bin sensitivity.** The shape of the histogram depends heavily on the number of bins you choose. Too few bins smooth away real pathologies; too many bins amplify noise. If the number of bins doesn't evenly divide the total number of ranks, some bins are expected to get slightly more counts than others, introducing artifacts.

---

#### A better alternative: the **ECDF plot** (shown above ↑)

The **Empirical Cumulative Distribution Function (ECDF)** sidesteps this problem entirely — it requires **no binning**. Every rank contributes directly to the curve. The light blue band shows the 95% confidence region. If the ranks are perfectly uniform, the ECDF stays inside the band.
        """)

if __name__ == "__main__":
    st.set_page_config(page_title="SBC Intuition", layout="centered")
    render()
