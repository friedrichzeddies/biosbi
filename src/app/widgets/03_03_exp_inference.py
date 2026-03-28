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


def get_simulation_defaults(simulator):
    config = simulator._config
    _, _, sigma_default = _range_defaults(config, "SIGMA", 0.5, 2.0)
    _, _, defocus_default = _range_defaults(config, "DEFOCUS", 0.5, 4.0)
    _, _, b_default = _range_defaults(config, "B_FACTOR", 0.5, 3.0)
    _, _, snr_default = _range_defaults(config, "SNR", 0.01, 0.5)
    amp_default = _as_float(config.get("AMP", 0.1), 0.1)
    return {
        "sigma": float(sigma_default),
        "amp": float(amp_default),
        "defocus": float(defocus_default),
        "b_factor": float(b_default),
        "snr": float(snr_default),
    }


def build_payload(simulator, state_prefix, defaults):
    num_models = len(simulator._models)

    st.subheader("Experiment Payload")
    st.markdown(
        "Choose simulation settings and send them as one payload to generate a never-seen test image."
    )

    # --- Preset System ---
    presets = {
        "Custom": None,
        "Default": defaults,
        "Clean": {
            "sigma": defaults["sigma"],
            "amp": defaults["amp"],
            "defocus": 0.5,
            "b_factor": 0.0,
            "snr": 1.0,
        },
        "High Noise": {
            "snr": 0.01,
        },
        "High Defocus": {
            "defocus": 4.0,
        },
    }
    
    if f"{state_prefix}_preset" not in st.session_state:
        st.session_state[f"{state_prefix}_preset"] = "Default"
        for k, v in presets["Default"].items():
            if f"{state_prefix}_{k}" not in st.session_state:
                st.session_state[f"{state_prefix}_{k}"] = v

    def _apply_preset():
        pname = st.session_state[f"{state_prefix}_preset"]
        if pname != "Custom":
            p_vals = presets[pname]
            for k, v in p_vals.items():
                st.session_state[f"{state_prefix}_{k}"] = v

    def _make_custom():
        st.session_state[f"{state_prefix}_preset"] = "Custom"

    selected_preset = st.selectbox(
        "Presets", 
        list(presets.keys()), 
        key=f"{state_prefix}_preset",
        on_change=_apply_preset
    )
    
    if selected_preset == "Default":
        st.success("Using the same imaging settings as training; no discrepancy expected.")
    elif selected_preset == "Clean":
        st.warning("Removing CTF effects and taking a low amount of noise. This is out-of-distribution for the model!")
    elif selected_preset == "High Noise":
        st.warning("Testing robustness: extremely low SNR. The model will likely be uncertain.")
    elif selected_preset == "High Defocus":
        st.warning("Testing robustness: extremely high defocus. The CTF oscillates rapidly.")

    # --- Payload UI ---
    c1, cx, cy, cz = st.columns(4)
    with c1:
        true_index = st.slider(
            "True conformation",
            min_value=0,
            max_value=max(0, num_models - 1),
            value=0,
            key=f"{state_prefix}_true_index",
        )

    with cx:
        rot_x = st.slider("Rot X (deg)", 0, 360, 0, key=f"{state_prefix}_rot_x", help="Rotation around the X-axis in degrees.")
    with cy:
        rot_y = st.slider("Rot Y (deg)", 0, 360, 45, key=f"{state_prefix}_rot_y", help="Rotation around the Y-axis in degrees.")
    with cz:
        rot_z = st.slider("Rot Z (deg)", 0, 360, 0, key=f"{state_prefix}_rot_z", help="Rotation around the Z-axis in degrees.")

    with st.expander("Direct access to CTF settings", expanded=(selected_preset == "Custom")):
        ec1, ec2 = st.columns(2)
        with ec1:
            defocus = st.number_input(
                "Defocus (μm)",
                value=float(defaults["defocus"]),
                step=0.05,
                key=f"{state_prefix}_defocus",
                on_change=_make_custom,
                help="The defocus of the microscope is given in units of micrometres (μm).",
            )
            b_factor = st.number_input(
                "B-factor (Å²)",
                value=float(defaults["b_factor"]),
                step=0.05,
                key=f"{state_prefix}_b_factor",
                on_change=_make_custom,
                help="The B-factor is given in units of Angström squared (Å²) and defines the decay rate of the CTF envelope function.",
            )

        with ec2:
            snr_linear = st.number_input(
                "SNR (linear)",
                min_value=1e-6,
                value=max(1e-6, float(defaults["snr"])),
                step=0.01,
                key=f"{state_prefix}_snr",
                on_change=_make_custom,
                help="The SNR (Signal-to-noise ratio) linear is the ratio of signal power to noise power. It defines the amount of noise in simulated images. For example, at SNR=1.0, signal and noise have equal power.",
            )
            sigma = st.number_input(
                "Sigma",
                value=float(defaults["sigma"]),
                step=0.05,
                key=f"{state_prefix}_sigma",
                on_change=_make_custom,
                help="The atom sigma defines the size of the Gaussians used to approximate the protein's electron density. Here, each Gaussian represents one amino acid, and while all Gaussians have the same sigma, the value is made to vary in the simulations.",
            )
            amp = st.number_input(
                "Amplitude contrast (AMP)",
                value=float(defaults["amp"]),
                step=0.01,
                key=f"{state_prefix}_amp",
                on_change=_make_custom,
                help="The Amplitude is a unitless parameter which ranges between 0 and 1.",
            )
            
            # CTF Popover
            with st.popover("Show CTF Preview"):
                pixel_size = float(simulator._pixel_size.item())
                k_1d = np.linspace(0, 1 / (2 * max(1e-6, pixel_size)), 100)
                k2 = k_1d**2
                env = np.exp(-b_factor * k2 * 0.5)
                phase = defocus * np.pi * 2.0 * 10000 * 0.019866
                ctf_val = (-amp * np.cos(phase * k2 * 0.5) - np.sqrt(max(0, 1 - amp**2)) * np.sin(phase * k2 * 0.5)) * env / max(1e-6, amp)
                
                fig_ctf, ax_ctf = plt.subplots(figsize=(4, 2))
                ax_ctf.plot(k_1d, ctf_val, color="#1f77b4", lw=1.5)
                ax_ctf.axhline(0, color="gray", lw=0.5, ls="--")
                ax_ctf.set_title("CTF Preview", fontsize=10)
                ax_ctf.tick_params(axis='both', which='major', labelsize=8)
                ax_ctf.set_xlabel("k (1/Å)", fontsize=8)
                plt.tight_layout()
                st.pyplot(fig_ctf)
                plt.close(fig_ctf)

    payload = {
        "index": int(true_index),
        "rotation_deg_xyz": [float(rot_x), float(rot_y), float(rot_z)],
        "sigma": float(sigma),
        "shift_xy": [0.0, 0.0],
        "defocus": float(defocus),
        "b_factor": float(b_factor),
        "amp": float(amp),
        "snr_linear": float(snr_linear),
        "snr_log10_internal": float(np.log10(max(1e-8, snr_linear))),
        "posterior_samples": 2000,
    }
    return payload


def randomize_payload_controls(simulator, state_prefix):
    config = simulator._config
    num_models = len(simulator._models)
    rng = np.random.default_rng()

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
    st.session_state[f"{state_prefix}_amp"] = _sample_uniform_or_scalar(config, "AMP", 0.05, 0.15, rng)

    st.session_state[f"{state_prefix}_rot_x"] = int(rng.integers(0, 361))
    st.session_state[f"{state_prefix}_rot_y"] = int(rng.integers(0, 361))
    st.session_state[f"{state_prefix}_rot_z"] = int(rng.integers(0, 361))

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
        round(float(payload["defocus"]), 6),
        round(float(payload["b_factor"]), 6),
        round(float(payload["amp"]), 6),
        round(float(payload["snr_linear"]), 6),
    )


@st.fragment
def render_ui():

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

    selected_model_name = st.selectbox("Cached models:", available_models)
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
    result_key = f"exp_result_{selected_model_name}"
    resample_flag_key = f"exp_resample_ref_{selected_model_name}"
    random_flag_key = f"exp_randomize_{selected_model_name}"
    reset_flag_key = f"exp_reset_{selected_model_name}"
    ref_params_key = f"exp_ref_params_{selected_model_name}"

    def _request_reference_resample():
        st.session_state[resample_flag_key] = True

    def _request_random_config():
        st.session_state[random_flag_key] = True
        
    def _request_reset():
        st.session_state[reset_flag_key] = True

    # --- Pre-calculate defaults and handle state logic BEFORE building widgets ---
    defaults = get_simulation_defaults(simulator)

    # Apply randomization (only if NOT instantiated)
    if st.session_state.get(random_flag_key, False):
        randomize_payload_controls(simulator, state_prefix)
        st.session_state[f"{state_prefix}_preset"] = "Custom"
        st.session_state[random_flag_key] = False
        st.rerun()

    # Apply reset (only if NOT instantiated)
    if st.session_state.get(reset_flag_key, False):
        st.session_state[f"{state_prefix}_sigma"] = defaults["sigma"]
        st.session_state[f"{state_prefix}_amp"] = defaults["amp"]
        st.session_state[f"{state_prefix}_defocus"] = defaults["defocus"]
        st.session_state[f"{state_prefix}_b_factor"] = defaults["b_factor"]
        st.session_state[f"{state_prefix}_snr"] = defaults["snr"]
        st.session_state[f"{state_prefix}_preset"] = "Default"
        st.session_state[reset_flag_key] = False
        st.rerun()

    payload = build_payload(simulator, state_prefix=state_prefix, defaults=defaults)

    control_col1, control_col2, control_col3 = st.columns([1, 1, 1])
    with control_col1:
        st.button("Random configuration", on_click=_request_random_config)
    with control_col2:
        st.button("Resample training reference", on_click=_request_reference_resample)
    with control_col3:
        st.button("Return to default values", on_click=_request_reset)

    # --- Synchronized Rotation Management ---
    quat_np = R.from_euler("xyz", payload["rotation_deg_xyz"], degrees=True).as_quat()
    quat_tensor = torch.tensor([quat_np], dtype=torch.float32)

    # --- Reference Parameter Management ---
    resample_requested = bool(st.session_state.get(resample_flag_key, False))
    need_new_ref_params = (
        st.session_state.get(ref_params_key) is None
        or st.session_state[ref_params_key]["index"] != payload["index"]
        or resample_requested
    )

    if need_new_ref_params:
        p = simulator._priors.sample((1,))
        st.session_state[ref_params_key] = {
            "index": int(payload["index"]),
            "sigma": p[2].clone(),
            "shift": p[3].clone(),
            "defocus": p[4].clone(),
            "b_factor": p[5].clone(),
            "amp": p[6].clone(),
            "snr": p[7].clone(),
        }
        st.session_state[resample_flag_key] = False
    
    ref_p = st.session_state[ref_params_key]

    # --- Image Generation (Synchronized) ---
    ref_noisy = cryo_em_simulator(
        simulator._models,
        torch.tensor([[ref_p["index"]]], dtype=torch.float32),
        quat_tensor,
        ref_p["sigma"],
        ref_p["shift"],
        ref_p["defocus"],
        ref_p["b_factor"],
        ref_p["amp"],
        ref_p["snr"],
        simulator._num_pixels,
        simulator._pixel_size,
    )
    ref_clean = project_density(
        simulator._models[[ref_p["index"]]],
        quat_tensor,
        ref_p["sigma"],
        ref_p["shift"],
        simulator._num_pixels,
        simulator._pixel_size,
    )

    exp_noisy = cryo_em_simulator(
        simulator._models,
        torch.tensor([[payload["index"]]], dtype=torch.float32),
        quat_tensor,
        torch.tensor([[payload["sigma"]]], dtype=torch.float32),
        torch.tensor([[0.0, 0.0]], dtype=torch.float32),
        torch.tensor([[payload["defocus"]]], dtype=torch.float32),
        torch.tensor([[payload["b_factor"]]], dtype=torch.float32),
        torch.tensor([[payload["amp"]]], dtype=torch.float32),
        torch.tensor([[payload["snr_log10_internal"]]], dtype=torch.float32),
        simulator._num_pixels,
        simulator._pixel_size,
    )
    exp_clean = project_density(
        simulator._models[[payload["index"]]],
        quat_tensor,
        torch.tensor([[payload["sigma"]]], dtype=torch.float32),
        torch.tensor([[0.0, 0.0]], dtype=torch.float32),
        simulator._num_pixels,
        simulator._pixel_size,
    )

    overlay_clean = st.checkbox("Overlay clean density on noisy images", value=False)

    col_img1, col_img2 = st.columns(2, border=True)
    with col_img1:
        st.markdown("**Reference Sample** (Training Distribution)")
        fig, ax = plt.subplots(figsize=(4, 4))
        ref_noisy_np = ref_noisy[0].numpy()
        ax.imshow(ref_noisy_np, cmap="gray")
        if overlay_clean:
            ref_clean_np = ref_clean[0].numpy()
            masked_clean = np.ma.masked_where(ref_clean_np < ref_clean_np.max() * 0.1, ref_clean_np)
            ax.imshow(masked_clean, cmap="hot", alpha=0.45)
        ax.set_title(f"True state: {ref_p['index']}")
        ax.axis("off")
        st.pyplot(fig)
        plt.close(fig)

    with col_img2:
        st.markdown("**Experiment Sample** (User Defined)")
        fig, ax = plt.subplots(figsize=(4, 4))
        exp_noisy_np = exp_noisy[0].numpy()
        ax.imshow(exp_noisy_np, cmap="gray")
        if overlay_clean:
            exp_clean_np = exp_clean[0].numpy()
            masked_clean = np.ma.masked_where(exp_clean_np < exp_clean_np.max() * 0.1, exp_clean_np)
            ax.imshow(masked_clean, cmap="hot", alpha=0.45)
        ax.set_title(f"True state: {payload['index']}")
        ax.axis("off")
        st.pyplot(fig)
        plt.close(fig)

    if posterior is None:
        st.info("No estimator found. Inference disabled.")
        return
    
    # --- Auto-run Inference ---
    current_signature = _payload_signature(payload)
    need_inference = (
        result_key not in st.session_state 
        or st.session_state[result_key].get("payload_signature") != current_signature
        or need_new_ref_params
    )
    
    if need_inference:
        with st.spinner("Sampling posterior..."):
            ref_theta_samples, _, ref_summary = infer_single_observation(
                posterior,
                ref_noisy,
                2000,
                ref_p["index"],
                num_models,
            )
            exp_theta_samples, _, exp_summary = infer_single_observation(
                posterior,
                exp_noisy,
                2000,
                payload["index"],
                num_models,
            )

            st.session_state[result_key] = {
                "payload_signature": current_signature,
                "ref_theta_samples": ref_theta_samples,
                "ref_summary": ref_summary,
                "exp_theta_samples": exp_theta_samples,
                "exp_summary": exp_summary,
                "ref_true_index": ref_p["index"],
            }

    inference_res = st.session_state[result_key]
    ref_theta_samples = inference_res["ref_theta_samples"]
    ref_summary = inference_res["ref_summary"]
    exp_theta_samples = inference_res["exp_theta_samples"]
    exp_summary = inference_res["exp_summary"]

    # --- Posterior Visualization ---
    _, center_col, _ = st.columns([1, 8, 1])
    with center_col:
        fig, ax = plt.subplots(figsize=(10, 5))

        sns.kdeplot(
            ref_theta_samples,
            ax=ax,
            fill=True,
            color="#1f77b4",
            label=f"Reference Posterior (Model {inference_res['ref_true_index']})",
            warn_singular=False,
        )
        sns.kdeplot(
            exp_theta_samples,
            ax=ax,
            fill=True,
            color="#ff7f0e",
            label=f"Experiment Posterior (Model {payload['index']})",
            warn_singular=False,
        )
        
        target_idx = payload["index"]
        ax.axvspan(target_idx - 0.5, target_idx + 0.5, color="#2ca02c", alpha=0.1, label="Ideal Range (Uniform)")

        ax.errorbar(ref_summary["posterior_mean"], 0.1, xerr=ref_summary["posterior_std"], fmt='|', color="#1f77b4", capsize=3, elinewidth=2, markeredgewidth=2, label="Reference Mean ± Std")
        ax.errorbar(exp_summary["posterior_mean"], 0.1, xerr=exp_summary["posterior_std"], fmt='|', color="#ff7f0e", capsize=3, elinewidth=2, markeredgewidth=2, label="Experiment Mean ± Std")

        ax.set_title("Continuous Posterior Density Comparison")
        ax.set_xlim(-0.5, num_models - 0.5)

        ticks = []
        labels = []
        for idx in range(num_models):
            boundary = idx - 0.5
            ticks.append(boundary)
            labels.append("")
            ticks.append(idx)
            labels.append(f"Model {idx}")
            ax.axvline(boundary, color="gray", linestyle="--", alpha=0.3)

        ax.axvline(num_models - 0.5, color="gray", linestyle="--", alpha=0.3)
        ticks.append(num_models - 0.5)
        labels.append("")

        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
        ax.legend(loc="upper right", prop={"size": 8})
        ax.set_ylabel("Density")
        st.pyplot(fig)
        plt.close(fig)
        
    with st.expander("🧪 Interesting things to try"):
        st.markdown(r"""
            There’s a lot of sliders to handle! To guide your exploration, we’ve included several presets:

            - **Default:** Here, the experimental values (used in the right image) are the same as the ones the model was trained on (used in the left image). The two posteriors should match up quite well. Try modifying the imaging parameters directly and increasing the SNR (thus reducing noise); you'll see the posterior converge more tightly on the correct bin. Interestingly, even with very little noise, the model still struggles to differentiate between late-stage conformations—proving that some ambiguity is inherent (shouldn't be suprising after seeing the embedding experiment, right?)!
            
            - **Clean:** What happens if we remove the effect of the microscope entirely and test our model on clean projections?? By decreasing CTF effects and noise, we get projections that are almost human-understandable. You might expect this to help the model, but remember: the model was never trained on "clean" images. While it still works for the standing cat, it often becomes **confidently wrong** for lying-down poses—predicting an incorrect model with extremely high confidence.
            
            - **High Noise / High Defocus:** Here we stress the model by making the image quality worse. Performance drops as expected, but interestingly, the model is also far less confident (the posterior broadens). It’s often better to have a model that knows it's uncertain than one that is confidently incorrect!
        """)


if __name__ == "__main__":
    render_ui()
