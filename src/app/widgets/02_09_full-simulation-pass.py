import os
import hashlib

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import torch
from scipy.spatial.transform import Rotation

from cryo_sbi import CryoEmSimulator
from cryo_sbi.wpa_simulator.cryo_em_simulator import cryo_em_simulator
from cryo_sbi.wpa_simulator.image_generation import project_density


BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "Chapter 2 - BioEM")


@st.cache_resource
def load_simulator():
    sim_json = os.path.join(BASE_DIR, "cat_proj_params.json")
    if not os.path.exists(sim_json):
        raise FileNotFoundError(f"Missing simulation config: {sim_json}")
    return CryoEmSimulator(sim_json, device="cpu")


def _as_scalar(value, fallback):
    if value is None:
        return float(fallback)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (list, tuple)) and len(value) > 0:
        return float(value[0])
    if torch.is_tensor(value):
        return float(value.flatten()[0].item())
    return float(fallback)


def _as_range(value, fallback_min, fallback_max):
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        lo = float(value[0])
        hi = float(value[1])
        return (min(lo, hi), max(lo, hi))
    val = _as_scalar(value, fallback_min)
    return (float(val), float(fallback_max))


def _ensure_slider_range(lo, hi, fallback_lo, fallback_hi):
    lo = float(lo)
    hi = float(hi)
    if hi > lo:
        return lo, hi
    return float(fallback_lo), float(fallback_hi)


def _ensure_reasonable_range(lo, hi, fallback_lo, fallback_hi, min_span):
    lo, hi = _ensure_slider_range(lo, hi, fallback_lo, fallback_hi)
    if (hi - lo) < float(min_span):
        return float(fallback_lo), float(fallback_hi)
    return lo, hi


def _to_numpy(image_tensor):
    return image_tensor[0].detach().cpu().numpy()


def _get_plot_limits(image_np):
    lo = float(np.percentile(image_np, 1))
    hi = float(np.percentile(image_np, 99))
    if hi <= lo:
        hi = lo + 1e-6
    return lo, hi


def _quat_wxyz_from_euler(rx, ry, rz):
    quat_xyzw = Rotation.from_euler("xyz", [rx, ry, rz], degrees=True).as_quat()
    return torch.tensor(
        [[quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]],
        dtype=torch.float32,
    )


def _build_clean_projection(simulator, model_idx, quaternion_wxyz, sigma, shift):
    model_index = torch.tensor([[float(model_idx)]], dtype=torch.float32)
    models_selected = simulator._models[model_index.round().long().flatten()]

    clean_projection = project_density(
        models_selected,
        quaternion_wxyz,
        sigma,
        shift,
        simulator._num_pixels,
        simulator._pixel_size,
    )
    return clean_projection


def _run_full_simulation_pass(simulator, sampled_parameters):
    return cryo_em_simulator(
        simulator._models,
        *sampled_parameters,
        simulator._num_pixels,
        simulator._pixel_size,
    )


def _slider_with_safe_range(label, lo, hi, default, step, key):
    value = float(np.clip(default, lo, hi))
    return st.slider(label, lo, hi, value, step=step, key=key)


def _slider_step(lo, hi, base_steps=300, min_step=1e-6):
    span = float(hi) - float(lo)
    if span <= 0:
        return float(min_step)
    return max(span / float(base_steps), float(min_step))


def _seed_from_values(values):
    key = "|".join([str(v) for v in values])
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


@st.fragment
def render(instance_id: str = "main"):
    st.subheader("Full Cryo-EM Cat Simulation")
    st.write(
        "Control the full image-formation chain: projection, CTF filtering, with a focus on now newly introduced noise. As a little sneak-peak, you can already change the conformation (we'll explain shortly) of the cat!"
    )

    try:
        simulator = load_simulator()
    except Exception as exc:
        st.error(str(exc))
        return

    def _k(name: str) -> str:
        return f"full_pass_{instance_id}_{name}"

    model_count = int(simulator.max_index) + 1
    sigma_min, sigma_max = _as_range(simulator._config.get("SIGMA", [0.5, 5.0]), 0.5, 5.0)
    defocus_min, defocus_max = _as_range(simulator._config.get("DEFOCUS", [0.5, 2.0]), 0.5, 2.0)
    b_factor_min, b_factor_max = _as_range(simulator._config.get("B_FACTOR", [1.0, 100.0]), 1.0, 100.0)
    snr_linear_min, snr_linear_max = _as_range(simulator._config.get("SNR", [0.001, 30.0]), 0.001, 30.0)
    amp_value = float(np.clip(_as_scalar(simulator._config.get("AMP", 0.1), 0.1), 1e-6, 0.99))
    shift_limit = float(abs(_as_scalar(simulator._config.get("SHIFT", 0.0), 0.0)))

    sigma_min, sigma_max = _ensure_reasonable_range(sigma_min, sigma_max, 0.5, 5.0, min_span=0.05)
    defocus_min, defocus_max = _ensure_reasonable_range(defocus_min, defocus_max, 0.5, 2.0, min_span=0.05)
    b_factor_min, b_factor_max = _ensure_reasonable_range(b_factor_min, b_factor_max, 1.0, 100.0, min_span=0.5)
    snr_linear_min, snr_linear_max = _ensure_reasonable_range(
        snr_linear_min,
        snr_linear_max,
        0.001,
        30.0,
        min_span=1e-4,
    )
    snr_linear_min = max(float(snr_linear_min), 1e-6)
    snr_linear_max = max(float(snr_linear_max), snr_linear_min + 1e-6)

    col1, col2, col3 = st.columns([1.05, 1.0, 1.0])

    with col1:
        st.markdown("### Controls")

        if model_count <= 1:
            model_idx = 0
            st.caption("Conformation Index fixed: 0")
        else:
            model_idx = st.slider("Conformation Index", 0, model_count - 1, 0, key=_k("model"))

        sigma_default = float(np.clip(1.0, sigma_min, sigma_max))
        defocus_default = float(np.clip(1.0, defocus_min, defocus_max))
        b_factor_default = float(np.clip(10.0, b_factor_min, b_factor_max))
        snr_default = float(np.clip(0.1, snr_linear_min, snr_linear_max))

        st.markdown("#### Noise")
        snr_linear_val = _slider_with_safe_range(
            "SNR (linear)",
            snr_linear_min,
            snr_linear_max,
            snr_default,
            step=_slider_step(snr_linear_min, snr_linear_max, base_steps=250, min_step=1e-4),
            key=_k("snr_linear"),
        )

        with st.expander("Rotation and Shift", expanded=False):
            rx = st.slider("Rotation X (deg)", -180, 180, 0, key=_k("rx"))
            ry = st.slider("Rotation Y (deg)", -180, 180, 90, key=_k("ry"))
            rz = st.slider("Rotation Z (deg)", -180, 180, 90, key=_k("rz"))

            if shift_limit > 0.0:
                shift_step = max(shift_limit / 100.0, 0.1)
                shift_x = st.slider(
                    "Shift X (px)",
                    -shift_limit,
                    shift_limit,
                    0.0,
                    step=shift_step,
                    key=_k("shift_x"),
                )
                shift_y = st.slider(
                    "Shift Y (px)",
                    -shift_limit,
                    shift_limit,
                    0.0,
                    step=shift_step,
                    key=_k("shift_y"),
                )
            else:
                shift_x = 0.0
                shift_y = 0.0

        with st.expander("CTF and Optics", expanded=False):
            sigma_val = _slider_with_safe_range(
                "Sigma",
                sigma_min,
                sigma_max,
                sigma_default,
                step=_slider_step(sigma_min, sigma_max, base_steps=250, min_step=0.01),
                key=_k("sigma"),
            )
            defocus_val = _slider_with_safe_range(
                "Defocus",
                defocus_min,
                defocus_max,
                defocus_default,
                # Defocus is linear in this simulator; avoid ultra-fine step sizes that make the UI feel broken.
                step=_slider_step(defocus_min, defocus_max, base_steps=150, min_step=0.01),
                key=_k("defocus"),
            )
            b_factor_val = _slider_with_safe_range(
                "B-factor",
                b_factor_min,
                b_factor_max,
                b_factor_default,
                step=_slider_step(b_factor_min, b_factor_max, base_steps=200, min_step=0.1),
                key=_k("b_factor"),
            )

        shift = torch.tensor([[float(shift_x), float(shift_y)]], dtype=torch.float32)
        amp = torch.tensor([[amp_value]], dtype=torch.float32)

        index = torch.tensor([[float(model_idx)]], dtype=torch.float32)
        quaternion = _quat_wxyz_from_euler(rx, ry, rz)
        sigma = torch.tensor([[float(sigma_val)]], dtype=torch.float32)
        defocus = torch.tensor([[float(defocus_val)]], dtype=torch.float32)
        b_factor = torch.tensor([[float(b_factor_val)]], dtype=torch.float32)
        snr = torch.tensor([[float(np.log10(max(snr_linear_val, 1e-6)))]], dtype=torch.float32)
        sampled_parameters = [index, quaternion, sigma, shift, defocus, b_factor, amp, snr]

        # Keep noise stable for the same parameter set; noise only changes when inputs change.
        noise_seed = _seed_from_values(
            [
                instance_id,
                model_idx,
                rx,
                ry,
                rz,
                shift_x,
                shift_y,
                sigma_val,
                defocus_val,
                b_factor_val,
                snr_linear_val,
            ]
        )
        rng_state = torch.get_rng_state()
        torch.manual_seed(noise_seed)

        clean_img = _build_clean_projection(
            simulator,
            model_idx,
            quaternion,
            sigma,
            shift,
        )
        full_pass_img = _run_full_simulation_pass(simulator, sampled_parameters)
        torch.set_rng_state(rng_state)


    with col2:
        st.markdown("### Clean Projection")

        clean_np = _to_numpy(clean_img)
        lo_clean, hi_clean = _get_plot_limits(clean_np)

        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.imshow(clean_np, cmap="gray", vmin=lo_clean, vmax=hi_clean)
        ax1.set_title("Clean Projection")
        ax1.axis("off")
        st.pyplot(fig1, clear_figure=True)
        plt.close(fig1)

    with col3:
        st.markdown("### Full Pass")

        final_np = _to_numpy(full_pass_img)
        lo_final, hi_final = _get_plot_limits(final_np)

        fig3, ax3 = plt.subplots(figsize=(4, 4))
        ax3.imshow(final_np, cmap="gray", vmin=lo_final, vmax=hi_final)
        ax3.set_title("Projection + CTF + Noise")
        ax3.axis("off")
        st.pyplot(fig3, clear_figure=True)
        plt.close(fig3)


def full_simulation_widget():
    """Backward-compatible alias used by older pages."""
    render(instance_id="legacy")


if __name__ == "__main__":
    st.set_page_config(page_title="Full Cat Simulation Pass", layout="wide")
    render(instance_id="standalone")
