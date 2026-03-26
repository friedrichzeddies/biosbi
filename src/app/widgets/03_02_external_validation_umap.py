import json
import importlib
import os

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import torch
from scipy.spatial import cKDTree
from scipy.spatial import ConvexHull

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


def _compute_umap_quality_metrics(z_sim_2d, z_ext_2d):
    """Return compact overlap/separation metrics for a user-facing verdict."""
    centroid_dist = float(np.linalg.norm(z_sim_2d.mean(axis=0) - z_ext_2d.mean(axis=0)))

    spread = float(np.sqrt(np.var(z_sim_2d, axis=0).sum() + np.var(z_ext_2d, axis=0).sum()))
    normalized_centroid = centroid_dist / (spread + 1e-8)

    sim_tree = cKDTree(z_sim_2d)
    ext_tree = cKDTree(z_ext_2d)

    sim_within = sim_tree.query(z_sim_2d, k=2)[0][:, 1]
    ext_within = ext_tree.query(z_ext_2d, k=2)[0][:, 1]
    sim_cross = ext_tree.query(z_sim_2d, k=1)[0]
    ext_cross = sim_tree.query(z_ext_2d, k=1)[0]

    # >1 means points are closer to their own cloud than the opposite cloud.
    nn_separation = float(
        0.5 * (np.median(sim_cross / (sim_within + 1e-8)) + np.median(ext_cross / (ext_within + 1e-8)))
    )

    try:
        hull_sim = ConvexHull(z_sim_2d)
        hull_ext = ConvexHull(z_ext_2d)
        hull_ratio = float(min(hull_sim.volume, hull_ext.volume) / max(hull_sim.volume, hull_ext.volume))
    except Exception:
        hull_ratio = None

    return centroid_dist, normalized_centroid, nn_separation, hull_ratio


def _build_verdict(misspecified, norm_centroid, nn_separation):
    """Map metrics to a compact and intuitive good/bad judgement."""
    strong_separation = norm_centroid >= 1.0 and nn_separation >= 1.15
    weak_separation = norm_centroid < 0.6 and nn_separation < 1.05

    if misspecified and strong_separation:
        return "good", "Good", "Misspecification is clearly visible in latent space."
    if misspecified and weak_separation:
        return "bad", "Needs Attention", "Misspecification was expected but overlap is still strong."
    if (not misspecified) and weak_separation:
        return "good", "Good", "No misspecification and good overlap; behavior is consistent."
    if (not misspecified) and strong_separation:
        return "bad", "Needs Attention", "No misspecification expected, but the clouds are clearly separated."

    return "warn", "Intermediate", "Some separation is present, but not decisive."


def _render_umap_results(result):
    z_sim_2d = result["z_sim_2d"]
    z_ext_2d = result["z_ext_2d"]

    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    ax.scatter(
        z_sim_2d[:, 0],
        z_sim_2d[:, 1],
        s=7,
        alpha=0.42,
        color="#1f77b4",
        label="In-distribution",
    )
    ax.scatter(
        z_ext_2d[:, 0],
        z_ext_2d[:, 1],
        s=7,
        alpha=0.42,
        color="#ff7f0e",
        label="External",
    )
    ax.set_title("Joint UMAP Latent Projection")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.legend(loc="best")
    st.pyplot(fig, use_container_width=False)
    plt.close(fig)

    st.markdown("### Result Summary")
    v1, v2, v3 = st.columns(3)
    with v1:
        st.metric("Centroid distance", f"{result['centroid_dist']:.3f}")
    with v2:
        st.metric("Normalized separation", f"{result['normalized_centroid']:.3f}")
    with v3:
        st.metric("NN separation ratio", f"{result['nn_separation']:.3f}")

    if result["verdict_kind"] == "good":
        st.success(f"{result['verdict_title']}: {result['verdict_text']}")
    elif result["verdict_kind"] == "bad":
        st.error(f"{result['verdict_title']}: {result['verdict_text']}")
    else:
        st.warning(f"{result['verdict_title']}: {result['verdict_text']}")

    st.caption(
        "Scenario label: "
        + ("misspecified" if result["misspecified"] else "not misspecified")
        + ". UMAP is qualitative, not a formal hypothesis test."
    )

    with st.expander("Interpretation help and thresholds", expanded=False):
        st.write(result["reason"])
        if result["overlap_volume_ratio"] is not None:
            st.write(
                f"Hull overlap ratio: {result['overlap_volume_ratio']:.3f} "
                "(closer to 1 means stronger geometric overlap)."
            )
        st.markdown(
            "#### Key points:\n"
            "- **Local ≫ Global:** UMAP preserves local neighborhoods perfectly, but global distances are distorted.\n"
            "  Separation ≠ proof of difference; overlap ≠ proof of similarity.\n\n"
            "- **Primary decision rule here:**\n"
            "  Good if expected scenario (misspecified or not) matches measured separation.\n\n"
            "- **Sample Size Matters:** Rare modes only appear with sufficient images.\n"
            "  Use 1000+ for stable judgement, 200-500 for quick checks.\n\n"
            "- **Complementary Test:** UMAP is *not* a statistical test. For definitive answers,\n"
            "  use the **MMD widget** (quantitative + p-value)."
        )


@st.fragment
def render_ui():
    st.title("External Validation: Latent UMAP Overlap")
    st.caption(
        "Guided flow: 1) Configure scenario, 2) Run projection, 3) Read the verdict card. "
        "Runtime depends on your machine and can range from a few seconds to about a minute."
    )

    base_dir, model_names = _available_model_dirs()
    if len(model_names) == 0:
        st.error("No model folders found in app/data/models.")
        return

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        trained_model_name = st.selectbox("Embedding network from model", model_names, key="umap_trained_model")
    with c2:
        mode = st.selectbox(
            "External misspecification mode",
            ["Parameter shift", "Structure shift"],
            key="umap_mode"
        )
    with c3:
        num_images = st.slider("Images per dataset", 100, 3000, 1000, step=100, key="umap_num_images")

    model_dir = os.path.join(base_dir, trained_model_name)

    try:
        trained_simulator, posterior, train_params = load_embedding_assets(model_dir)
    except Exception as err:
        st.error(f"Failed to load trained simulator/estimator for {trained_model_name}: {err}")
        return

    batch_size = st.slider("Simulation batch size", 50, 1000, 250, step=50, key="umap_batch_size")

    structure_simulator = None
    alt_name = trained_model_name
    
    # Initialize session state defaults if not present
    if "umap_sigma_scale" not in st.session_state:
        st.session_state.umap_sigma_scale = 1.0
    if "umap_shift_scale" not in st.session_state:
        st.session_state.umap_shift_scale = 1.0
    if "umap_defocus_scale" not in st.session_state:
        st.session_state.umap_defocus_scale = 1.0
    if "umap_b_factor_scale" not in st.session_state:
        st.session_state.umap_b_factor_scale = 1.0
    if "umap_snr_scale" not in st.session_state:
        st.session_state.umap_snr_scale = 1.0

    with cfg_right:
        # Step 1b: Shift controls
        if mode == "Parameter shift":
            st.markdown("Parameter Shift Preset")
            preset_options = [
                "Manual",
                "Conservative (Mild shift)",
                "Moderate (Medium shift)",
                "Aggressive (Strong shift)",
                "Overblur (Only sigma)",
                "Low SNR (Only noise)",
            ]
            
            preset = st.selectbox(
                "Select a preset or choose Manual to customize:",
                preset_options,
                key="umap_preset",
                on_change=_apply_preset,
                help="Scale the parameters by a **factor** to _fabricate_ an experiment."
            )

            if "umap_sync_slider_keys" not in st.session_state:
                st.session_state.umap_sync_slider_keys = False

            if "umap_slider_sigma" not in st.session_state:
                st.session_state.umap_slider_sigma = st.session_state.umap_sigma_scale
            if "umap_slider_shift" not in st.session_state:
                st.session_state.umap_slider_shift = st.session_state.umap_shift_scale
            if "umap_slider_defocus" not in st.session_state:
                st.session_state.umap_slider_defocus = st.session_state.umap_defocus_scale
            if "umap_slider_bfactor" not in st.session_state:
                st.session_state.umap_slider_bfactor = st.session_state.umap_b_factor_scale
            if "umap_slider_snr" not in st.session_state:
                st.session_state.umap_slider_snr = st.session_state.umap_snr_scale

            if st.session_state.umap_sync_slider_keys:
                st.session_state.umap_slider_sigma = st.session_state.umap_sigma_scale
                st.session_state.umap_slider_shift = st.session_state.umap_shift_scale
                st.session_state.umap_slider_defocus = st.session_state.umap_defocus_scale
                st.session_state.umap_slider_bfactor = st.session_state.umap_b_factor_scale
                st.session_state.umap_slider_snr = st.session_state.umap_snr_scale
                st.session_state.umap_sync_slider_keys = False

            with st.expander("Shift parameter controls", expanded=True):
                p1, p2 = st.columns(2)
                with p1:
                    st.slider("Sigma scale", 0.1, 5.0, step=0.1, key="umap_slider_sigma")
                    st.slider("Shift scale", 0.1, 5.0, step=0.1, key="umap_slider_shift")
                    st.slider("Defocus scale", 0.1, 5.0, step=0.1, key="umap_slider_defocus")
                with p2:
                    st.slider("B-factor scale", 0.1, 5.0, step=0.1, key="umap_slider_bfactor")
                    st.slider("SNR scale", 0.1, 5.0, step=0.1, key="umap_slider_snr")

                if st.button("Reset manual values to 1.0", key="umap_reset_manual", use_container_width=True):
                    _reset_manual_scales()
                    st.rerun()

            sigma_scale = st.session_state.umap_slider_sigma
            shift_scale = st.session_state.umap_slider_shift
            defocus_scale = st.session_state.umap_slider_defocus
            b_factor_scale = st.session_state.umap_slider_bfactor
            snr_scale = st.session_state.umap_slider_snr

            st.session_state.umap_sigma_scale = sigma_scale
            st.session_state.umap_shift_scale = shift_scale
            st.session_state.umap_defocus_scale = defocus_scale
            st.session_state.umap_b_factor_scale = b_factor_scale
            st.session_state.umap_snr_scale = snr_scale

    if mode == "Structure shift":
        default_alt = model_names[0]
        if len(model_names) > 1 and model_names[0] == trained_model_name:
            default_alt = model_names[1]
        alt_name = st.selectbox(
            "External structure source model",
            model_names,
            index=model_names.index(default_alt),
            key="umap_alt_name"
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
            "Example: sigma scale = 1.5 means each sampled sigma is multiplied by 1.5."
        )
        p1, p2, p3, p4, p5 = st.columns(5)
        with p1:
            sigma_scale = st.slider("Sigma scale (x sampled sigma)", 0.1, 5.0, 1.0, step=0.1, key="umap_sigma_scale")
        with p2:
            shift_scale = st.slider("Shift scale (x sampled shift)", 0.1, 5.0, 1.0, step=0.1, key="umap_shift_scale")
        with p3:
            defocus_scale = st.slider("Defocus scale (x sampled defocus)", 0.1, 5.0, 1.0, step=0.1, key="umap_defocus_scale")
        with p4:
            b_factor_scale = st.slider("B-factor scale (x sampled B-factor)", 0.1, 5.0, 1.0, step=0.1, key="umap_b_factor_scale")
        with p5:
            snr_scale = st.slider("SNR scale (x linear SNR)", 0.1, 5.0, 1.0, step=0.1, key="umap_snr_scale")

    if mode == "Parameter shift":
        misspecified = any(
            abs(v - 1.0) > 1e-9
            for v in [sigma_scale, shift_scale, defocus_scale, b_factor_scale, snr_scale]
        )
        reason = (
            f"External data is labeled **misspecified** by construction (σ={sigma_scale:.2f}x, "
            f"shift={shift_scale:.2f}x, defocus={defocus_scale:.2f}x, B-factor={b_factor_scale:.2f}x, SNR={snr_scale:.2f}x)."
            if misspecified
            else "External data is NOT misspecified: all parameter scales are 1.0."
        )
    else:
        misspecified = alt_name != trained_model_name
        reason = (
            f"External data is labeled **misspecified**: structures from `{alt_name}` (≠ `{trained_model_name}`)."
            if misspecified
            else "External data is NOT misspecified: same structure source."
        )

    with cfg_right:
        st.markdown("Scenario label")
        if misspecified:
            st.warning(reason)
        else:
            st.info(reason)

    st.caption(
        "Important: In this widget, 'misspecified' is a scenario label set by your controls. "
        "UMAP itself is not a formal hypothesis test and does not 'fail' statistically."
    )

    n1, n2 = st.columns(2)
    with n1:
        n_neighbors = st.slider("UMAP n_neighbors", 5, 100, 30, key="umap_n_neighbors")
    with n2:
        min_dist = st.slider("UMAP min_dist", 0.0, 0.99, 0.1, step=0.01, key="umap_min_dist")

    run_btn = st.button("Generate datasets and run UMAP", type="primary", key="umap_run_btn")

    if not run_btn:
        if "umap_cached_result" in st.session_state:
            st.info("Showing cached UMAP result from the last run. Click 'Run UMAP validation' to refresh.")
            _render_umap_results(st.session_state.umap_cached_result)
        else:
            st.info("Set misspecification controls, then run UMAP.")
        return

    try:
        umap_module = importlib.import_module("umap.umap_")
    except Exception:
        st.error(
            "UMAP is not available in this environment. Run `uv sync` to install `umap-learn`, then rerun this widget."
        )
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
        ).numpy()
        z_ext = est_utils.compute_latent_repr(
            estimator=posterior,
            images=ext_images,
            batch_size=batch_size,
            device="cpu",
        ).numpy()

    with st.spinner("Running UMAP projection (step 3/3)..."):
        z_joint = np.concatenate([z_sim, z_ext], axis=0)
        reducer = umap_module.UMAP(
            n_neighbors=min(n_neighbors, z_joint.shape[0] - 1),
            min_dist=min_dist,
            random_state=42,
        )
        z_2d = reducer.fit_transform(z_joint)

    z_sim_2d = z_2d[: z_sim.shape[0]]
    z_ext_2d = z_2d[z_sim.shape[0] :]

    centroid_dist, normalized_centroid, nn_separation, overlap_volume_ratio = _compute_umap_quality_metrics(
        z_sim_2d,
        z_ext_2d,
    )
    verdict_kind, verdict_title, verdict_text = _build_verdict(
        misspecified,
        normalized_centroid,
        nn_separation,
    )

    result = {
        "z_sim_2d": z_sim_2d,
        "z_ext_2d": z_ext_2d,
        "centroid_dist": centroid_dist,
        "normalized_centroid": normalized_centroid,
        "nn_separation": nn_separation,
        "overlap_volume_ratio": overlap_volume_ratio,
        "verdict_kind": verdict_kind,
        "verdict_title": verdict_title,
        "verdict_text": verdict_text,
        "misspecified": misspecified,
        "reason": reason,
    }
    st.session_state.umap_cached_result = result
    _render_umap_results(result)


if __name__ == "__main__":
    st.set_page_config(page_title="External Validation: UMAP", layout="wide")
    render_ui()
