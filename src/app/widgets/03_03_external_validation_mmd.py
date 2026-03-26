import json
import os

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import torch

import cryo_sbi.utils.estimator_utils as est_utils
from cryo_sbi.wpa_simulator.cryo_em_simulator import CryoEmSimulator, cryo_em_simulator




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


def mmd_permutation_p_value(
    z1,
    z2,
    epsilon,
    num_permutations=100,
    rng=None,
    return_null_distribution=False,
):
    x = torch.as_tensor(z1, dtype=torch.float32)
    y = torch.as_tensor(z2, dtype=torch.float32)
    observed = compute_mmd2_fixed_epsilon(x, y, epsilon)

    pooled = torch.cat([x, y], dim=0)
    n = x.shape[0]
    exceed = 0
    null_values = []
    for _ in range(num_permutations):
        perm = torch.randperm(pooled.shape[0], generator=rng) if rng is not None else torch.randperm(pooled.shape[0])
        x_p = pooled[perm[:n]]
        y_p = pooled[perm[n:]]
        val = compute_mmd2_fixed_epsilon(x_p, y_p, epsilon)
        if return_null_distribution:
            null_values.append(val)
        if val >= observed:
            exceed += 1

    p_value = (exceed + 1) / (num_permutations + 1)
    return observed, p_value, exceed, null_values


def _build_mmd_verdict(misspecified, reject_h0):
    """Map MMD test outcome to an intuitive user-facing verdict."""
    if misspecified and reject_h0:
        return "good", "Good", "Expected mismatch detected: latent distributions are significantly different."
    if misspecified and (not reject_h0):
        return (
            "warn",
            "Intermediate",
            "Misspecification was expected, but evidence was not strong enough to reject H0.",
        )
    if (not misspecified) and (not reject_h0):
        return "good", "Good", "No unexpected mismatch detected: distributions are statistically consistent."

    return "bad", "Needs Attention", "Unexpected mismatch detected despite non-misspecified setup."


def _render_mmd_results(result):
    st.markdown("### Result Summary")
    metrics = st.columns(3)
    metrics[0].metric("Permutation p-value", f"{result['p_value']:.4f}")
    metrics[1].metric("Two-sample test", "Reject H0" if result["reject_h0"] else "Do not reject H0")
    metrics[2].metric("MMD^2", f"{result['mmd2']:.6f}")

    if result["verdict_kind"] == "good":
        st.success(f"{result['verdict_title']}: {result['verdict_text']}")
    elif result["verdict_kind"] == "bad":
        st.error(f"{result['verdict_title']}: {result['verdict_text']}")
    else:
        st.warning(f"{result['verdict_title']}: {result['verdict_text']}")

    st.caption(
        "Scenario label: "
        + ("misspecified" if result["misspecified"] else "not misspecified")
        + ". MMD is a formal test: p-value below alpha implies statistically significant mismatch."
    )

    with st.expander("How to read this without confusion", expanded=False):
        st.write(result["reason"])
        st.markdown(
            "#### Key points:\n"
            "- **Scenario label** is determined by your controls (construction), not by statistics.\n"
            "- **MMD test decision** comes from p-value versus alpha (evidence in data).\n"
            "- Misspecified-by-construction data may still not reject H0 if shift is weak/noisy.\n"
            "- Non-misspecified setup can occasionally reject H0 due to finite-sample randomness.\n"
            "- Use both together: generation context + test decision for robust interpretation."
        )

    with st.expander("Optional: Statistical interpretation and reproducibility", expanded=False):
        left, right = st.columns(2, gap="medium")
        with left:
            st.markdown(
                "Permutation interpretation:\n"
                f"- Observed $MMD^2$: **{result['observed_mmd2']:.6f}**\n"
                f"- Null exceedances: **{result['exceed']} / {result['num_permutations']}**\n"
                f"- Computed p-value: $({result['exceed']} + 1) / ({result['num_permutations']} + 1) = {result['p_value']:.6f}$"
            )

            if result["deterministic_permutations"]:
                st.caption(
                    f"Reproducibility active: seed={int(result['permutation_seed'])}, "
                    f"subset size={result['k']}, permutations={result['num_permutations']}."
                )
            else:
                st.caption("Reproducibility off: random subset and permutation draws vary between runs.")

        with right:
            if result["show_permutation_plot"] and len(result["null_distribution"]) > 0:
                critical = float(np.quantile(np.asarray(result["null_distribution"]), 1.0 - result["alpha"]))
                fig, ax = plt.subplots(figsize=(4.8, 2.8))
                ax.hist(result["null_distribution"], bins=24, alpha=0.6, color="#1f77b4", label="Permutation null")
                ax.axvline(result["observed_mmd2"], color="#d62728", linewidth=2, label="Observed")
                ax.axvline(critical, color="#ff7f0e", linewidth=2, linestyle="--", label="Critical")
                ax.set_title("Null Distribution of MMD^2")
                ax.set_xlabel("MMD^2")
                ax.set_ylabel("Count")
                ax.legend(loc="best", fontsize=8)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            else:
                st.info("Enable 'Show permutation null-distribution plot' to display the diagnostic plot.")


@st.fragment
def render_ui():
    st.title("External Validation: Latent MMD")
    st.caption(
        "Guided flow: 1) Configure scenario, 2) Run statistical test, 3) Read the verdict card. "
        "MMD gives a formal two-sample decision via permutation p-value."
    )

    base_dir, model_names = _available_model_dirs()
    if len(model_names) == 0:
        st.error("No model folders found in app/data/models.")
        return

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        trained_model_name = st.selectbox("Embedding network from model", model_names, key="mmd_trained_model")
    with c2:
        mode = st.selectbox(
            "External misspecification mode",
            ["Parameter shift", "Structure shift"],
            key="mmd_mode"
        )
    with c3:
        num_images = st.slider("Images per dataset", 100, 3000, 1000, step=100, key="mmd_num_images")

    model_dir = os.path.join(base_dir, trained_model_name)

    try:
        trained_simulator, posterior, _ = load_embedding_assets(model_dir)
    except Exception as err:
        st.error(f"Failed to load trained simulator/estimator for {trained_model_name}: {err}")
        return

    batch_size = st.slider("Simulation batch size", 50, 1000, 250, step=50, key="mmd_batch_size")

    t1, t2, t3 = st.columns(3)
    with t1:
        alpha = st.slider("Test significance alpha", 0.001, 0.2, 0.05, step=0.001, key="mmd_alpha")
    with t2:
        num_permutations = st.slider("Permutation samples", 20, 300, 100, step=10, key="mmd_num_permutations")
    with t3:
        perm_subset = st.slider("Permutation subset size", 100, 1000, 400, step=50, key="mmd_perm_subset")

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
            key="mmd_alt_name"
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
            sigma_scale = st.slider("Sigma scale (x sampled sigma)", 0.1, 5.0, 1.0, step=0.1, key="mmd_sigma_scale")
        with p2:
            shift_scale = st.slider("Shift scale (x sampled shift)", 0.1, 5.0, 1.0, step=0.1, key="mmd_shift_scale")
        with p3:
            defocus_scale = st.slider("Defocus scale (x sampled defocus)", 0.1, 5.0, 1.0, step=0.1, key="mmd_defocus_scale")
        with p4:
            b_factor_scale = st.slider("B-factor scale (x sampled B-factor)", 0.1, 5.0, 1.0, step=0.1, key="mmd_b_factor_scale")
        with p5:
            snr_scale = st.slider("SNR scale (x linear SNR)", 0.1, 5.0, 1.0, step=0.1, key="mmd_snr_scale")

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

    with cfg_right:
        st.markdown("Scenario label")
        if misspecified:
            st.warning(reason)
        else:
            st.info(reason)

    run_btn = st.button("Generate datasets and compute MMD", type="primary", key="mmd_run_btn")

    if not run_btn:
        if "mmd_cached_result" in st.session_state:
            st.info("Showing cached MMD result from the last run. Click 'Run MMD validation' to refresh.")
            _render_mmd_results(st.session_state.mmd_cached_result)
        else:
            st.info("Set misspecification controls, then run MMD.")
        return

    with st.spinner("Simulating datasets (step 1/3)..."):
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

    with st.spinner("Computing latent embeddings (step 2/3)..."):
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

    with st.spinner("Running MMD test (step 3/3)..."):
        mmd2, _, epsilon = compute_mmd_gaussian_median(z_sim, z_ext)

        rng = None
        if deterministic_permutations:
            rng = torch.Generator(device="cpu")
            rng.manual_seed(int(permutation_seed))

        k = min(perm_subset, z_sim.shape[0], z_ext.shape[0])
        idx_sim = torch.randperm(z_sim.shape[0], generator=rng)[:k] if rng is not None else torch.randperm(z_sim.shape[0])[:k]
        idx_ext = torch.randperm(z_ext.shape[0], generator=rng)[:k] if rng is not None else torch.randperm(z_ext.shape[0])[:k]
        z_sim_perm = z_sim[idx_sim]
        z_ext_perm = z_ext[idx_ext]
        observed_mmd2, p_value, exceed, null_distribution = mmd_permutation_p_value(
            z_sim_perm,
            z_ext_perm,
            epsilon,
            num_permutations=num_permutations,
            rng=rng,
            return_null_distribution=show_permutation_plot,
        )
        reject_h0 = p_value < alpha

    verdict_kind, verdict_title, verdict_text = _build_mmd_verdict(misspecified, reject_h0)
    result = {
        "p_value": p_value,
        "reject_h0": reject_h0,
        "mmd2": mmd2,
        "verdict_kind": verdict_kind,
        "verdict_title": verdict_title,
        "verdict_text": verdict_text,
        "misspecified": misspecified,
        "reason": reason,
        "observed_mmd2": observed_mmd2,
        "exceed": exceed,
        "num_permutations": num_permutations,
        "deterministic_permutations": deterministic_permutations,
        "permutation_seed": permutation_seed,
        "k": k,
        "show_permutation_plot": show_permutation_plot,
        "null_distribution": null_distribution,
        "alpha": alpha,
    }
    st.session_state.mmd_cached_result = result
    _render_mmd_results(result)


if __name__ == "__main__":
    st.set_page_config(page_title="External Validation: MMD", layout="wide")
    render_ui()
