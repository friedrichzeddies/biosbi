import json
import os

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import torch

import cryo_sbi.utils.estimator_utils as est_utils
from cryo_sbi.wpa_simulator.cryo_em_simulator import CryoEmSimulator, cryo_em_simulator

st.set_page_config(page_title="External Validation: MMD", layout="wide")


def _available_model_dirs():
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "models")
    if not os.path.exists(base_dir):
        return base_dir, ["10cat_large_batch_resnet"]
    names = sorted(
        [
            name
            for name in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, name))
        ]
    )
    return base_dir, names


@st.cache_resource
def load_embedding_assets(model_dir):
    sim_json = os.path.join(model_dir, "simulation_parameters.json")
    train_json = os.path.join(model_dir, "training_parameters.json")
    estimator_pt = os.path.join(model_dir, "estimator.pt")

    simulator = CryoEmSimulator(sim_json, device="cpu")
    posterior = est_utils.load_estimator(train_json, estimator_pt, device="cpu")

    train_params = {}
    if os.path.exists(train_json):
        with open(train_json, "r", encoding="utf-8") as handle:
            train_params = json.load(handle)

    return simulator, posterior, train_params


@st.cache_resource
def load_simulator_only(model_dir):
    sim_json = os.path.join(model_dir, "simulation_parameters.json")
    simulator = CryoEmSimulator(sim_json, device="cpu")
    return simulator


def _simulate_param_shifted_images(
    simulator,
    num_images,
    batch_size,
    sigma_scale,
    shift_scale,
    defocus_scale,
    b_factor_scale,
    snr_scale,
):
    params = simulator._priors.sample((num_images,))

    params[2] = torch.clamp(params[2] * sigma_scale, min=1e-4)
    params[3] = params[3] * shift_scale
    params[4] = torch.clamp(params[4] * defocus_scale, min=1e-6)
    params[5] = torch.clamp(params[5] * b_factor_scale, min=1e-6)
    params[7] = params[7] + np.log10(max(1e-8, snr_scale))

    all_images = []
    for i in range(0, num_images, batch_size):
        idx = params[0][i : i + batch_size]
        quat = params[1][i : i + batch_size]
        sigma = params[2][i : i + batch_size]
        shift = params[3][i : i + batch_size]
        defocus = params[4][i : i + batch_size]
        b_factor = params[5][i : i + batch_size]
        amp = params[6][i : i + batch_size]
        snr = params[7][i : i + batch_size]

        batch_img = cryo_em_simulator(
            simulator._models,
            idx,
            quat,
            sigma,
            shift,
            defocus,
            b_factor,
            amp,
            snr,
            simulator._num_pixels,
            simulator._pixel_size,
        )
        all_images.append(batch_img.cpu())

    return torch.cat(all_images, dim=0)


def _generate_external_images(
    trained_simulator,
    mode,
    num_images,
    batch_size,
    structure_simulator=None,
    sigma_scale=1.0,
    shift_scale=1.0,
    defocus_scale=1.0,
    b_factor_scale=1.0,
    snr_scale=1.0,
):
    if mode == "Structure shift":
        return structure_simulator.simulate(num_images, batch_size=batch_size)

    return _simulate_param_shifted_images(
        trained_simulator,
        num_images,
        batch_size,
        sigma_scale,
        shift_scale,
        defocus_scale,
        b_factor_scale,
        snr_scale,
    )


def compute_mmd_gaussian_median(z1, z2):
    x = torch.as_tensor(z1, dtype=torch.float32)
    y = torch.as_tensor(z2, dtype=torch.float32)

    n = x.shape[0]
    m = y.shape[0]

    d_xy = torch.cdist(x, y, p=2).pow(2)
    epsilon = torch.median(d_xy).clamp_min(1e-12)

    k_xy = torch.exp(-d_xy / epsilon)
    d_xx = torch.cdist(x, x, p=2).pow(2)
    d_yy = torch.cdist(y, y, p=2).pow(2)
    k_xx = torch.exp(-d_xx / epsilon)
    k_yy = torch.exp(-d_yy / epsilon)

    term_xx = (k_xx.sum() - k_xx.diag().sum()) / max(n * (n - 1), 1)
    term_yy = (k_yy.sum() - k_yy.diag().sum()) / max(m * (m - 1), 1)
    term_xy = k_xy.mean()

    mmd2 = term_xx + term_yy - 2.0 * term_xy
    mmd2 = torch.clamp(mmd2, min=0.0)

    return float(mmd2.item()), float(torch.sqrt(mmd2).item()), float(epsilon.item())


def compute_mmd2_fixed_epsilon(z1, z2, epsilon):
    x = torch.as_tensor(z1, dtype=torch.float32)
    y = torch.as_tensor(z2, dtype=torch.float32)

    n = x.shape[0]
    m = y.shape[0]

    d_xy = torch.cdist(x, y, p=2).pow(2)
    d_xx = torch.cdist(x, x, p=2).pow(2)
    d_yy = torch.cdist(y, y, p=2).pow(2)

    k_xy = torch.exp(-d_xy / epsilon)
    k_xx = torch.exp(-d_xx / epsilon)
    k_yy = torch.exp(-d_yy / epsilon)

    term_xx = (k_xx.sum() - k_xx.diag().sum()) / max(n * (n - 1), 1)
    term_yy = (k_yy.sum() - k_yy.diag().sum()) / max(m * (m - 1), 1)
    term_xy = k_xy.mean()

    mmd2 = term_xx + term_yy - 2.0 * term_xy
    mmd2 = torch.clamp(mmd2, min=0.0)
    return float(mmd2.item())


def mmd_permutation_p_value(z1, z2, epsilon, num_permutations=100):
    x = torch.as_tensor(z1, dtype=torch.float32)
    y = torch.as_tensor(z2, dtype=torch.float32)
    observed = compute_mmd2_fixed_epsilon(x, y, epsilon)

    pooled = torch.cat([x, y], dim=0)
    n = x.shape[0]
    exceed = 0
    for _ in range(num_permutations):
        perm = torch.randperm(pooled.shape[0])
        x_p = pooled[perm[:n]]
        y_p = pooled[perm[n:]]
        val = compute_mmd2_fixed_epsilon(x_p, y_p, epsilon)
        if val >= observed:
            exceed += 1

    p_value = (exceed + 1) / (num_permutations + 1)
    return observed, p_value


@st.fragment
def render_ui():
    st.title("External Validation: Latent MMD")
    st.markdown(
        "This widget does the following:\n"
        "- Simulates an in-distribution dataset using the training simulator.\n"
        "- Simulates an external dataset under a chosen misspecification scenario.\n"
        "- Embeds both datasets with the same trained embedding network.\n"
        "- Computes Gaussian-kernel MMD and a permutation-test p-value for a quantitative two-sample decision."
    )
    st.markdown(
        "Quantitatively compare latent embeddings from in-distribution simulated data and misspecified "
        "external data using Gaussian-kernel MMD with median heuristic bandwidth."
    )

    base_dir, model_names = _available_model_dirs()
    if len(model_names) == 0:
        st.error("No model folders found in app/data/models.")
        return

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        trained_model_name = st.selectbox("Embedding network from model", model_names)
    with c2:
        mode = st.selectbox(
            "External misspecification mode",
            ["Parameter shift", "Structure shift"],
        )
    with c3:
        num_images = st.slider("Images per dataset", 100, 3000, 1000, step=100)

    model_dir = os.path.join(base_dir, trained_model_name)

    try:
        trained_simulator, posterior, train_params = load_embedding_assets(model_dir)
    except Exception as err:
        st.error(f"Failed to load trained simulator/estimator for {trained_model_name}: {err}")
        return

    batch_size = st.slider("Simulation batch size", 50, 1000, 250, step=50)

    t1, t2, t3 = st.columns(3)
    with t1:
        alpha = st.slider("Test significance alpha", 0.001, 0.2, 0.05, step=0.001)
    with t2:
        num_permutations = st.slider("Permutation samples", 20, 300, 100, step=10)
    with t3:
        perm_subset = st.slider("Permutation subset size", 100, 1000, 400, step=50)

    structure_simulator = None
    alt_name = trained_model_name
    sigma_scale = 1.0
    shift_scale = 1.0
    defocus_scale = 1.0
    b_factor_scale = 1.0
    snr_scale = 1.0

    if mode == "Structure shift":
        default_alt = model_names[0]
        if len(model_names) > 1 and model_names[0] == trained_model_name:
            default_alt = model_names[1]
        alt_name = st.selectbox(
            "External structure source model",
            model_names,
            index=model_names.index(default_alt),
        )
        alt_model_dir = os.path.join(base_dir, alt_name)
        try:
            structure_simulator = load_simulator_only(alt_model_dir)
        except Exception as err:
            st.error(f"Failed to load external structure simulator from {alt_name}: {err}")
            return
    else:
        st.info(
            "Parameter shift uses multiplicative scale factors, not absolute replacement values. "
            "Example: defocus scale = 0.8 means each sampled defocus is multiplied by 0.8."
        )
        p1, p2, p3, p4, p5 = st.columns(5)
        with p1:
            sigma_scale = st.slider("Sigma scale (x sampled sigma)", 0.1, 5.0, 1.0, step=0.1)
        with p2:
            shift_scale = st.slider("Shift scale (x sampled shift)", 0.1, 5.0, 1.0, step=0.1)
        with p3:
            defocus_scale = st.slider("Defocus scale (x sampled defocus)", 0.1, 5.0, 1.0, step=0.1)
        with p4:
            b_factor_scale = st.slider("B-factor scale (x sampled B-factor)", 0.1, 5.0, 1.0, step=0.1)
        with p5:
            snr_scale = st.slider("SNR scale (x linear SNR)", 0.1, 5.0, 1.0, step=0.1)

    if mode == "Parameter shift":
        misspecified = any(
            abs(v - 1.0) > 1e-9
            for v in [sigma_scale, shift_scale, defocus_scale, b_factor_scale, snr_scale]
        )
        reason = (
            "External data is labeled misspecified by construction because at least one "
            "parameter scale differs from 1.0."
            if misspecified
            else "External data is NOT labeled misspecified: all parameter scales are 1.0."
        )
    else:
        misspecified = alt_name != trained_model_name
        reason = (
            "External data is labeled misspecified by construction because structures are drawn "
            "from a different model folder."
            if misspecified
            else "External data is NOT labeled misspecified: external structure source equals training model."
        )

    st.markdown("Misspecification label status")
    if misspecified:
        st.warning(reason)
    else:
        st.info(reason)

    run_btn = st.button("Generate datasets and compute MMD", type="primary")

    if not run_btn:
        st.info("Set misspecification controls, then compute MMD.")
        return

    with st.spinner("Simulating datasets, computing latent embeddings, computing MMD..."):
        sim_images = trained_simulator.simulate(num_images, batch_size=batch_size)

        if mode == "Structure shift":
            ext_images = _generate_external_images(
                trained_simulator,
                mode,
                num_images,
                batch_size,
                structure_simulator=structure_simulator,
            )
        else:
            ext_images = _generate_external_images(
                trained_simulator,
                mode,
                num_images,
                batch_size,
                sigma_scale=sigma_scale,
                shift_scale=shift_scale,
                defocus_scale=defocus_scale,
                b_factor_scale=b_factor_scale,
                snr_scale=snr_scale,
            )

        z_sim = est_utils.compute_latent_repr(
            estimator=posterior,
            images=sim_images,
            batch_size=batch_size,
            device="cpu",
        )
        z_ext = est_utils.compute_latent_repr(
            estimator=posterior,
            images=ext_images,
            batch_size=batch_size,
            device="cpu",
        )

        mmd2, mmd, epsilon = compute_mmd_gaussian_median(z_sim, z_ext)

        k = min(perm_subset, z_sim.shape[0], z_ext.shape[0])
        idx_sim = torch.randperm(z_sim.shape[0])[:k]
        idx_ext = torch.randperm(z_ext.shape[0])[:k]
        z_sim_perm = z_sim[idx_sim]
        z_ext_perm = z_ext[idx_ext]
        observed_mmd2_sub, p_value = mmd_permutation_p_value(
            z_sim_perm,
            z_ext_perm,
            epsilon,
            num_permutations=num_permutations,
        )
        reject_h0 = p_value < alpha

    metrics = st.columns(5)
    metrics[0].metric("MMD^2", f"{mmd2:.6f}")
    metrics[1].metric("MMD", f"{mmd:.6f}")
    metrics[2].metric("Bandwidth epsilon", f"{epsilon:.6f}")
    metrics[3].metric("Permutation p-value", f"{p_value:.4f}")
    metrics[4].metric("Two-sample test", "Reject H0" if reject_h0 else "Do not reject H0")

    if reject_h0:
        st.error(
            "Failed test: MMD permutation two-sample test rejected H0 at the selected alpha, "
            "indicating a statistically significant distribution mismatch in latent space."
        )
    else:
        st.success(
            "No failed two-sample test at the selected alpha: the MMD permutation test did not reject H0."
        )

    st.caption(
        "If MMD rejects very often, this can be normal when misspecification is strong, sample size is large, "
        "or alpha is generous. For a baseline sanity check, set all scales to 1.0 (or same structure model) "
        "and rerun."
    )

    st.caption(
        "Interpretation: scenario label ('misspecified') is set by your controls, while test failure comes from "
        "the MMD permutation p-value. These are related but not identical concepts."
    )

    with st.expander("How to read this without confusion", expanded=False):
        st.markdown(
            "- Scenario label: tells how external data was generated (by construction).\n"
            "- Statistical test result: tells whether latent distributions differ significantly.\n"
            "- You can have misspecified-by-construction data without test rejection if shift is weak/noisy.\n"
            "- You can occasionally reject H0 under non-misspecified setup due to finite-sample randomness.\n"
            "- Use both: generation context + p-value decision."
        )

    z_sim_np = z_sim.numpy().flatten()
    z_ext_np = z_ext.numpy().flatten()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(
        z_sim_np,
        bins=80,
        density=True,
        alpha=0.45,
        color="#1f77b4",
        label="Simulated (in-distribution)",
    )
    ax.hist(
        z_ext_np,
        bins=80,
        density=True,
        alpha=0.45,
        color="#ff7f0e",
        label="External (misspecified)",
    )
    ax.set_title("Marginal latent value comparison")
    ax.set_xlabel("Latent value")
    ax.set_ylabel("Density")
    ax.legend(loc="best")
    st.pyplot(fig)
    plt.close(fig)


if __name__ == "__main__":
    render_ui()
