import json
import importlib
import os

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import torch

import cryo_sbi.utils.estimator_utils as est_utils
from cryo_sbi.wpa_simulator.cryo_em_simulator import CryoEmSimulator, cryo_em_simulator

st.set_page_config(page_title="External Validation: UMAP", layout="wide")


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


@st.fragment
def render_ui():
    st.title("External Validation: Latent UMAP Overlap")
    st.markdown(
        "This widget does the following:\n"
        "- Simulates an in-distribution dataset using the training simulator.\n"
        "- Simulates an external dataset under a chosen misspecification scenario.\n"
        "- Embeds both datasets with the same trained embedding network.\n"
        "- Runs a joint UMAP projection for qualitative overlap inspection."
    )
    st.markdown(
        "Compare latent embeddings of in-distribution simulated particles against a misspecified "
        "external dataset using a joint 2D UMAP projection."
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
            "Example: sigma scale = 1.5 means each sampled sigma is multiplied by 1.5."
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

    st.caption(
        "Important: In this widget, 'misspecified' is a scenario label set by your controls. "
        "UMAP itself is not a formal hypothesis test and does not 'fail' statistically."
    )

    n1, n2 = st.columns(2)
    with n1:
        n_neighbors = st.slider("UMAP n_neighbors", 5, 100, 30)
    with n2:
        min_dist = st.slider("UMAP min_dist", 0.0, 0.99, 0.1, step=0.01)

    run_btn = st.button("Generate datasets and run UMAP", type="primary")

    if not run_btn:
        st.info("Set misspecification controls, then run UMAP.")
        return

    try:
        umap_module = importlib.import_module("umap.umap_")
    except Exception:
        st.error(
            "UMAP is not available in this environment. Run `uv sync` to install `umap-learn`, then rerun this widget."
        )
        return

    with st.spinner("Simulating datasets, computing latent embeddings, running UMAP..."):
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
        ).numpy()
        z_ext = est_utils.compute_latent_repr(
            estimator=posterior,
            images=ext_images,
            batch_size=batch_size,
            device="cpu",
        ).numpy()

        z_joint = np.concatenate([z_sim, z_ext], axis=0)
        reducer = umap_module.UMAP(
            n_neighbors=min(n_neighbors, z_joint.shape[0] - 1),
            min_dist=min_dist,
            random_state=42,
        )
        z_2d = reducer.fit_transform(z_joint)

    z_sim_2d = z_2d[: z_sim.shape[0]]
    z_ext_2d = z_2d[z_sim.shape[0] :]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(
        z_sim_2d[:, 0],
        z_sim_2d[:, 1],
        s=8,
        alpha=0.45,
        color="#1f77b4",
        label="Simulated (in-distribution)",
    )
    ax.scatter(
        z_ext_2d[:, 0],
        z_ext_2d[:, 1],
        s=8,
        alpha=0.45,
        color="#ff7f0e",
        label="External (misspecified)",
    )
    ax.set_title("Joint UMAP of latent embeddings")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.legend(loc="best")
    st.pyplot(fig)
    plt.close(fig)

    centroid_dist = float(np.linalg.norm(z_sim_2d.mean(axis=0) - z_ext_2d.mean(axis=0)))
    st.write(f"2D centroid distance (UMAP space): {centroid_dist:.3f}")
    st.caption(
        "Interpretation: strong overlap suggests low misspecification. Clear separation or disjoint clouds "
        "suggest misspecification between training simulator and external data generation."
    )
    with st.expander("How to read this without being misled", expanded=False):
        st.markdown(
            "- UMAP preserves local neighborhoods, not global distances exactly.\n"
            "- Overlap is qualitative evidence of similarity, not proof of equal distributions.\n"
            "- Separation is a warning sign, but its strength depends on UMAP hyperparameters and sample size.\n"
            "- For a quantitative decision, use the companion MMD widget with p-value testing."
        )


if __name__ == "__main__":
    render_ui()
