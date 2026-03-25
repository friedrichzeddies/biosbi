import json
import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st
import torch
from scipy.spatial.transform import Rotation as R

import cryo_sbi.utils.estimator_utils as est_utils
from cryo_sbi.wpa_simulator.cryo_em_simulator import CryoEmSimulator, cryo_em_simulator
from cryo_sbi.wpa_simulator.image_generation import project_density

st.set_page_config(page_title="Experiment Inference", layout="wide")


def _as_float(value, fallback):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _range_defaults(config, key, fallback_low, fallback_high):
    value = config.get(key)
    if isinstance(value, list) and len(value) == 2:
        low = _as_float(value[0], fallback_low)
        high = _as_float(value[1], fallback_high)
        if low > high:
            low, high = high, low
        return low, high, 0.5 * (low + high)

    scalar = _as_float(value, 0.5 * (fallback_low + fallback_high))
    return scalar, scalar, scalar


def _sample_uniform_or_scalar(config, key, fallback_low, fallback_high, rng):
    low, high, default = _range_defaults(config, key, fallback_low, fallback_high)
    if high > low:
        return float(rng.uniform(low, high))
    return float(default)


def _sample_with_sane_fallback(
    config,
    key,
    cfg_fallback_low,
    cfg_fallback_high,
    sane_low,
    sane_high,
    rng,
):
    low, high, _ = _range_defaults(config, key, cfg_fallback_low, cfg_fallback_high)
    if (high - low) > 1e-12:
        return float(rng.uniform(low, high))
    return float(rng.uniform(sane_low, sane_high))


@st.cache_resource
def load_assets(model_dir):
    sim_json = os.path.join(model_dir, "simulation_parameters.json")
    train_json = os.path.join(model_dir, "training_parameters.json")
    estimator_pt = os.path.join(model_dir, "estimator.pt")

    simulator = CryoEmSimulator(sim_json, device="cpu")

    posterior = None
    if os.path.exists(train_json) and os.path.exists(estimator_pt):
        try:
            posterior = est_utils.load_estimator(
                train_json,
                estimator_pt,
                device="cpu",
            )
        except Exception as err:
            print(f"Failed to load posterior: {err}")

    train_params = {}
    if os.path.exists(train_json):
        with open(train_json, "r", encoding="utf-8") as handle:
            train_params = json.load(handle)

    return simulator, posterior, train_params


def build_payload(simulator, state_prefix):
    config = simulator._config
    num_models = len(simulator._models)

    sigma_low, sigma_high, sigma_default = _range_defaults(config, "SIGMA", 0.5, 2.0)
    defocus_low, defocus_high, defocus_default = _range_defaults(config, "DEFOCUS", 0.5, 4.0)
    b_low, b_high, b_default = _range_defaults(config, "B_FACTOR", 0.5, 3.0)
    snr_low, snr_high, snr_default = _range_defaults(config, "SNR", 0.01, 0.5)
    amp_default = _as_float(config.get("AMP", 0.1), 0.1)
    shift_default = _as_float(config.get("SHIFT", 0.0), 0.0)

    st.subheader("Experiment Payload")
    st.markdown(
        "Choose simulation settings and send them as one payload to generate a never-seen test image."
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        true_index = st.slider(
            "True conformation",
            min_value=0,
            max_value=max(0, num_models - 1),
            value=0,
            key=f"{state_prefix}_true_index",
        )
        sigma = st.number_input(
            "Sigma",
            value=float(sigma_default),
            step=0.05,
            key=f"{state_prefix}_sigma",
            help=f"Training reference range: [{sigma_low:.3f}, {sigma_high:.3f}]",
        )
        amp = st.number_input(
            "Amplitude contrast (AMP)",
            value=float(amp_default),
            step=0.01,
            key=f"{state_prefix}_amp",
        )

    with c2:
        rot_x = st.slider("Rot X (deg)", 0, 360, 0, key=f"{state_prefix}_rot_x")
        rot_y = st.slider("Rot Y (deg)", 0, 360, 45, key=f"{state_prefix}_rot_y")
        rot_z = st.slider("Rot Z (deg)", 0, 360, 0, key=f"{state_prefix}_rot_z")

    with c3:
        shift_x = st.number_input(
            "Shift X",
            value=float(shift_default),
            step=0.05,
            key=f"{state_prefix}_shift_x",
        )
        shift_y = st.number_input(
            "Shift Y",
            value=float(shift_default),
            step=0.05,
            key=f"{state_prefix}_shift_y",
        )
        defocus = st.number_input(
            "Defocus",
            value=float(defocus_default),
            step=0.05,
            key=f"{state_prefix}_defocus",
            help=f"Training reference range: [{defocus_low:.3f}, {defocus_high:.3f}]",
        )

    with c4:
        b_factor = st.number_input(
            "B-factor",
            value=float(b_default),
            step=0.05,
            key=f"{state_prefix}_b_factor",
            help=f"Training reference range: [{b_low:.3f}, {b_high:.3f}]",
        )
        snr_linear = st.number_input(
            "SNR (linear)",
            min_value=1e-6,
            value=max(1e-6, float(snr_default)),
            step=0.01,
            key=f"{state_prefix}_snr",
            help=f"Training reference range: [{snr_low:.3f}, {snr_high:.3f}]",
        )
        num_samples = st.slider(
            "Posterior samples",
            min_value=200,
            max_value=4000,
            value=1200,
            step=100,
            key=f"{state_prefix}_num_samples",
        )

    payload = {
        "index": int(true_index),
        "rotation_deg_xyz": [float(rot_x), float(rot_y), float(rot_z)],
        "sigma": float(sigma),
        "shift_xy": [float(shift_x), float(shift_y)],
        "defocus": float(defocus),
        "b_factor": float(b_factor),
        "amp": float(amp),
        "snr_linear": float(snr_linear),
        "snr_log10_internal": float(np.log10(max(1e-8, snr_linear))),
        "posterior_samples": int(num_samples),
    }
    return payload


def randomize_payload_controls(simulator, state_prefix):
    config = simulator._config
    num_models = len(simulator._models)
    rng = np.random.default_rng()

    shift_default = abs(_as_float(config.get("SHIFT", 0.0), 0.0))
    shift_bound = max(25.0, shift_default if shift_default > 0 else 25.0)

    amp_default = _as_float(config.get("AMP", 0.1), 0.1)
    amp_low = max(1e-4, amp_default * 0.5)
    amp_high = max(amp_low + 1e-4, amp_default * 1.5)

    st.session_state[f"{state_prefix}_true_index"] = int(rng.integers(0, max(1, num_models)))
    st.session_state[f"{state_prefix}_sigma"] = _sample_with_sane_fallback(
        config,
        "SIGMA",
        0.5,
        2.0,
        0.5,
        5.0,
        rng,
    )
    st.session_state[f"{state_prefix}_amp"] = float(rng.uniform(amp_low, amp_high))

    st.session_state[f"{state_prefix}_rot_x"] = int(rng.integers(0, 361))
    st.session_state[f"{state_prefix}_rot_y"] = int(rng.integers(0, 361))
    st.session_state[f"{state_prefix}_rot_z"] = int(rng.integers(0, 361))

    st.session_state[f"{state_prefix}_shift_x"] = float(rng.uniform(-shift_bound, shift_bound))
    st.session_state[f"{state_prefix}_shift_y"] = float(rng.uniform(-shift_bound, shift_bound))
    st.session_state[f"{state_prefix}_defocus"] = _sample_with_sane_fallback(
        config,
        "DEFOCUS",
        0.5,
        4.0,
        0.5,
        2.0,
        rng,
    )
    st.session_state[f"{state_prefix}_b_factor"] = _sample_with_sane_fallback(
        config,
        "B_FACTOR",
        0.5,
        3.0,
        1.0,
        100.0,
        rng,
    )
    st.session_state[f"{state_prefix}_snr"] = _sample_with_sane_fallback(
        config,
        "SNR",
        0.01,
        0.5,
        0.001,
        0.5,
        rng,
    )


def generate_image_from_payload(simulator, payload):
    idx_tensor = torch.tensor([[payload["index"]]], dtype=torch.float32)
    quat_np = R.from_euler("xyz", payload["rotation_deg_xyz"], degrees=True).as_quat()
    quat_tensor = torch.tensor([quat_np], dtype=torch.float32)

    sigma_tensor = torch.tensor([[payload["sigma"]]], dtype=torch.float32)
    shift_tensor = torch.tensor([payload["shift_xy"]], dtype=torch.float32)
    defocus_tensor = torch.tensor([[payload["defocus"]]], dtype=torch.float32)
    b_factor_tensor = torch.tensor([[payload["b_factor"]]], dtype=torch.float32)
    amp_tensor = torch.tensor([[payload["amp"]]], dtype=torch.float32)
    snr_tensor = torch.tensor([[payload["snr_log10_internal"]]], dtype=torch.float32)

    noisy = cryo_em_simulator(
        simulator._models,
        idx_tensor,
        quat_tensor,
        sigma_tensor,
        shift_tensor,
        defocus_tensor,
        b_factor_tensor,
        amp_tensor,
        snr_tensor,
        simulator._num_pixels,
        simulator._pixel_size,
    )

    clean = project_density(
        simulator._models[[payload["index"]]],
        quat_tensor,
        sigma_tensor,
        shift_tensor,
        simulator._num_pixels,
        simulator._pixel_size,
    )

    return noisy, clean


def summarize_predictions(theta_samples, true_index, num_models):
    preds = np.round(theta_samples).astype(int).clip(0, num_models - 1)
    counts = np.bincount(preds, minlength=num_models)

    top_idx = int(np.argmax(counts))
    top_prob = float(counts[top_idx] / max(1, len(preds)) * 100.0)
    true_prob = float(counts[true_index] / max(1, len(preds)) * 100.0)

    summary = {
        "posterior_mean": float(np.mean(theta_samples)),
        "posterior_std": float(np.std(theta_samples)),
        "rounded_true_state_prob_percent": true_prob,
        "top_predicted_state": top_idx,
        "top_predicted_state_prob_percent": top_prob,
    }
    return preds, summary


def sample_reference_from_training_prior(simulator, true_index):
    params = simulator._priors.sample((1,))

    index = torch.tensor([[true_index]], dtype=torch.float32)
    quaternion = params[1]
    sigma = params[2]
    shift = params[3]
    defocus = params[4]
    b_factor = params[5]
    amp = params[6]
    snr = params[7]

    noisy = cryo_em_simulator(
        simulator._models,
        index,
        quaternion,
        sigma,
        shift,
        defocus,
        b_factor,
        amp,
        snr,
        simulator._num_pixels,
        simulator._pixel_size,
    )

    idx_int = int(index[0, 0].round().item())
    clean = project_density(
        simulator._models[[idx_int]],
        quaternion,
        sigma,
        shift,
        simulator._num_pixels,
        simulator._pixel_size,
    )

    return noisy, clean, idx_int


def infer_single_observation(posterior, image, num_samples, true_index, num_models):
    samples = est_utils.sample_posterior(
        estimator=posterior,
        images=image,
        num_samples=num_samples,
        batch_size=num_samples,
        device="cpu",
    )
    theta_samples = samples[:, 0].detach().cpu().numpy()
    preds, summary = summarize_predictions(theta_samples, true_index, num_models)
    return theta_samples, preds, summary


def _payload_signature(payload):
    return (
        int(payload["index"]),
        round(float(payload["rotation_deg_xyz"][0]), 6),
        round(float(payload["rotation_deg_xyz"][1]), 6),
        round(float(payload["rotation_deg_xyz"][2]), 6),
        round(float(payload["sigma"]), 6),
        round(float(payload["shift_xy"][0]), 6),
        round(float(payload["shift_xy"][1]), 6),
        round(float(payload["defocus"]), 6),
        round(float(payload["b_factor"]), 6),
        round(float(payload["amp"]), 6),
        round(float(payload["snr_linear"]), 6),
        int(payload["posterior_samples"]),
    )


@st.fragment
def render_ui():
    st.title("03 Experiment Inference")
    st.markdown(
        "Use one trained posterior as the fixed model and stress-test it with custom simulation payloads "
        "that can differ from the training simulation setup."
    )

    models_base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "models")
    if os.path.exists(models_base_dir):
        available_models = sorted(
            [
                folder
                for folder in os.listdir(models_base_dir)
                if os.path.isdir(os.path.join(models_base_dir, folder))
            ]
        )
    else:
        available_models = ["10cat_large_batch_resnet"]

    selected_model_name = st.selectbox("Posterior trained on", available_models)
    model_dir = os.path.join(models_base_dir, selected_model_name)

    try:
        simulator, posterior, train_params = load_assets(model_dir)
    except Exception as err:
        st.error(f"Could not load assets for {selected_model_name}: {err}")
        return

    num_models = len(simulator._models)
    st.write(
        "Loaded estimator model with "
        f"{num_models} conformations. "
        f"Theta shift={train_params.get('THETA_SHIFT', 'N/A')}, "
        f"theta scale={train_params.get('THETA_SCALE', 'N/A')}."
    )

    state_prefix = f"exp_{selected_model_name}"
    preview_key = f"exp_preview_{selected_model_name}"
    result_key = f"exp_result_{selected_model_name}"
    resample_flag_key = f"exp_resample_ref_{selected_model_name}"
    random_flag_key = f"exp_randomize_{selected_model_name}"

    def _request_reference_resample():
        st.session_state[resample_flag_key] = True

    def _request_random_config():
        st.session_state[random_flag_key] = True

    # Important: apply randomization before payload widgets are instantiated,
    # otherwise Streamlit forbids mutating those session keys in the same run.
    random_requested = bool(st.session_state.get(random_flag_key, False))
    if random_requested:
        randomize_payload_controls(simulator, state_prefix)
        st.session_state[random_flag_key] = False
        st.rerun()

    payload = build_payload(simulator, state_prefix=state_prefix)

    control_col1, control_col2 = st.columns([1, 1])
    with control_col1:
        st.button("Random configuration", on_click=_request_random_config)
    with control_col2:
        st.markdown("")

    current_signature = _payload_signature(payload)
    existing_preview = st.session_state.get(preview_key)
    resample_requested = bool(st.session_state.get(resample_flag_key, False))

    need_new_reference = (
        existing_preview is None
        or existing_preview["ref_true_index"] != payload["index"]
        or resample_requested
    )

    if need_new_reference:
        ref_noisy, ref_clean, ref_true_idx = sample_reference_from_training_prior(
            simulator,
            payload["index"],
        )
    else:
        ref_noisy = existing_preview["ref_noisy"]
        ref_clean = existing_preview["ref_clean"]
        ref_true_idx = existing_preview["ref_true_index"]

    need_new_experiment = (
        existing_preview is None
        or existing_preview.get("payload_signature") != current_signature
    )
    if need_new_experiment:
        exp_noisy, exp_clean = generate_image_from_payload(simulator, payload)
    else:
        exp_noisy = existing_preview["exp_noisy"]
        exp_clean = existing_preview["exp_clean"]

    preview = {
        "payload": payload,
        "payload_signature": current_signature,
        "ref_noisy": ref_noisy,
        "ref_clean": ref_clean,
        "ref_true_index": ref_true_idx,
        "exp_noisy": exp_noisy,
        "exp_clean": exp_clean,
    }
    st.session_state[preview_key] = preview
    st.session_state[resample_flag_key] = False
        
    result = preview

    overlay_clean = st.checkbox("Overlay clean density on noisy images", value=False)

    col_img1, col_img2 = st.columns(2, border=True)
    with col_img1:
        st.markdown("Training-config reference sample")
        fig, ax = plt.subplots(figsize=(4, 4))
        ref_noisy_np = result["ref_noisy"][0].numpy()
        ax.imshow(ref_noisy_np, cmap="gray")
        if overlay_clean:
            ref_clean_np = result["ref_clean"][0].numpy()
            masked_clean = np.ma.masked_where(ref_clean_np < ref_clean_np.max() * 0.1, ref_clean_np)
            ax.imshow(masked_clean, cmap="hot", alpha=0.45)
        ax.set_title(f"True state: {result['ref_true_index']}")
        ax.axis("off")
        st.pyplot(fig)
        plt.close(fig)

    with col_img2:
        st.markdown("User-defined experiment sample")
        fig, ax = plt.subplots(figsize=(4, 4))
        exp_noisy_np = result["exp_noisy"][0].numpy()
        ax.imshow(exp_noisy_np, cmap="gray")
        if overlay_clean:
            exp_clean_np = result["exp_clean"][0].numpy()
            masked_clean = np.ma.masked_where(exp_clean_np < exp_clean_np.max() * 0.1, exp_clean_np)
            ax.imshow(masked_clean, cmap="hot", alpha=0.45)
        ax.set_title(f"True state: {result['payload']['index']}")
        ax.axis("off")
        st.pyplot(fig)
        plt.close(fig)

    if posterior is None:
        st.info(
            "No estimator.pt and training_parameters.json found for this model directory. "
            "Image generation works, but posterior inference is disabled."
        )
        return
    
    control_col1, control_col2 = st.columns([1, 1])
    with control_col1:
        st.button("Resample training reference", on_click=_request_reference_resample)
    with control_col2:
        run_inference = st.button(
            "Compute posterior for current preview",
            type="primary",
            disabled=posterior is None,
        )

    if run_inference:
        with st.spinner("Sampling posterior for currently displayed images..."):
            ref_theta_samples, ref_preds, ref_summary = infer_single_observation(
                posterior,
                preview["ref_noisy"],
                payload["posterior_samples"],
                preview["ref_true_index"],
                num_models,
            )
            exp_theta_samples, exp_preds, exp_summary = infer_single_observation(
                posterior,
                preview["exp_noisy"],
                payload["posterior_samples"],
                payload["index"],
                num_models,
            )

            st.session_state[result_key] = {
                **preview,
                "ref_theta_samples": ref_theta_samples,
                "ref_preds": ref_preds,
                "ref_summary": ref_summary,
                "exp_theta_samples": exp_theta_samples,
                "exp_preds": exp_preds,
                "exp_summary": exp_summary,
            }

    if result_key not in st.session_state:
        st.info(
            "Adjust controls and inspect the images first, then click 'Compute posterior for current preview'."
        )
        return

    result = st.session_state[result_key]
    if result.get("payload_signature") != current_signature:
        st.warning(
            "Posterior plots are from a previous preview. Click 'Compute posterior for current preview' to refresh."
        )

    ref_theta_samples = result["ref_theta_samples"]
    ref_preds = result["ref_preds"]
    ref_summary = result["ref_summary"]
    exp_theta_samples = result["exp_theta_samples"]
    exp_preds = result["exp_preds"]
    exp_summary = result["exp_summary"]

    st.subheader("Posterior comparison: reference vs experiment")

    mcol1, mcol2 = st.columns(2, border=True)
    with mcol1:
        st.markdown("Reference sample metrics")
        st.markdown(f"True state: **{result['ref_true_index']}**")
        st.markdown(f"Posterior mean: **{ref_summary['posterior_mean']:.3f}**")
        st.markdown(f"Posterior std: **{ref_summary['posterior_std']:.3f}**")
        st.markdown(
            f"P(rounded=true): **{ref_summary['rounded_true_state_prob_percent']:.1f}%**"
        )
        st.markdown(
            "Top class: "
            f"**{ref_summary['top_predicted_state']} "
            f"({ref_summary['top_predicted_state_prob_percent']:.1f}%)**"
        )
    with mcol2:
        st.markdown("Experiment sample metrics")
        st.markdown(f"True state: **{result['payload']['index']}**")
        st.markdown(f"Posterior mean: **{exp_summary['posterior_mean']:.3f}**")
        st.markdown(f"Posterior std: **{exp_summary['posterior_std']:.3f}**")
        st.markdown(
            f"P(rounded=true): **{exp_summary['rounded_true_state_prob_percent']:.1f}%**"
        )
        st.markdown(
            "Top class: "
            f"**{exp_summary['top_predicted_state']} "
            f"({exp_summary['top_predicted_state_prob_percent']:.1f}%)**"
        )

    plot_col1, plot_col2 = st.columns([2, 1])

    with plot_col1:
        fig, ax = plt.subplots(figsize=(8, 3))
        sns.kdeplot(
            ref_theta_samples,
            ax=ax,
            fill=True,
            color="#1f77b4",
            label=f"Reference (true={result['ref_true_index']})",
            warn_singular=False,
        )
        sns.kdeplot(
            exp_theta_samples,
            ax=ax,
            fill=True,
            color="#ff7f0e",
            label=f"Experiment (true={result['payload']['index']})",
            warn_singular=False,
        )
        ax.set_title("Continuous posterior over conformation index")
        ax.set_xlim(-0.5, num_models - 0.5)

        ticks = []
        labels = []
        for idx in range(num_models):
            boundary = idx - 0.5
            ticks.append(boundary)
            labels.append(f"{boundary:.1f}")
            ticks.append(idx)
            labels.append(f"Model {idx}")
            ax.axvline(boundary, color="gray", linestyle="--", alpha=0.4)

        ax.axvline(num_models - 0.5, color="gray", linestyle="--", alpha=0.4)
        ticks.append(num_models - 0.5)
        labels.append(f"{num_models - 0.5:.1f}")

        ax.set_xticks(ticks)
        ax.set_xticklabels(labels, rotation=45 if num_models > 4 else 0)
        ax.axvline(result["ref_true_index"], color="#1f77b4", linestyle="-", alpha=0.8)
        ax.axvline(result["payload"]["index"], color="#ff7f0e", linestyle="-", alpha=0.8)
        if num_models <= 10:
            ax.legend(loc="upper right", prop={"size": 8})
        ax.set_ylabel("Density")
        st.pyplot(fig)
        plt.close(fig)

    with plot_col2:
        fig, ax = plt.subplots(figsize=(4, 3))
        bins = np.arange(-0.5, num_models + 0.5, 1)
        ref_weights = np.ones_like(ref_preds) / max(1, len(ref_preds)) * 100.0
        exp_weights = np.ones_like(exp_preds) / max(1, len(exp_preds)) * 100.0
        ax.hist(
            [ref_preds, exp_preds],
            bins=bins,
            weights=[ref_weights, exp_weights],
            color=["#1f77b4", "#ff7f0e"],
            label=["Reference", "Experiment"],
            align="mid",
        )
        ax.set_title("Discrete predictions")
        ax.set_ylabel("Percentage (%)")
        ax.set_xticks(range(num_models))
        ax.set_xticklabels([str(i) for i in range(num_models)])
        ax.set_xlim(-0.5, num_models - 0.5)
        if num_models <= 10:
            ax.legend(loc="upper right", prop={"size": 8})
        st.pyplot(fig)
        plt.close(fig)

    with st.expander("How to interpret these posterior plots", expanded=False):
        st.markdown(
            "- KDE plot (left): each curve is the continuous posterior over conformation index.\\n"
            "- Vertical solid lines: the true conformation index used for each sample.\\n"
            "- Good adaptation: the experiment (orange) curve peaks near its true-state line and resembles the reference (blue) sharpness.\\n"
            "- Domain shift signs: experiment curve broadens, shifts away from the true line, or becomes multi-modal compared with the reference.\\n"
            "- Histogram (right): rounded class probabilities in percent; compare how much mass remains on the true class for reference vs experiment."
        )


if __name__ == "__main__":
    render_ui()
