import os

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import torch
from scipy.spatial.transform import Rotation

from cryo_sbi import CryoEmSimulator
from cryo_sbi.wpa_simulator.ctf import apply_ctf
from cryo_sbi.wpa_simulator.image_generation import project_density


BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "Chapter 2 - BioEM")
DISPLAY_DPI = 180
IMAGE_INTERPOLATION = "lanczos"


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
    return (float(fallback_min), float(fallback_max))


def _build_clean_cat_projection(simulator, model_idx, rx, ry, rz):
    sigma_val = _as_scalar(simulator._config.get("SIGMA", [1.0]), 1.0)
    shift_val = _as_scalar(simulator._config.get("SHIFT", 0.0), 0.0)

    sigma = torch.tensor([sigma_val], dtype=torch.float32)
    shift = torch.tensor([[shift_val, shift_val]], dtype=torch.float32)

    quat_xyzw = Rotation.from_euler("xyz", [rx, ry, rz], degrees=True).as_quat()
    quat_wxyz = torch.tensor(
        [[quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]],
        dtype=torch.float32,
    )

    model_index = torch.tensor([[float(model_idx)]], dtype=torch.float32)
    models_selected = simulator._models[model_index.round().long().flatten()]

    clean_projection = project_density(
        models_selected,
        quat_wxyz,
        sigma,
        shift,
        simulator._num_pixels,
        simulator._pixel_size,
    )
    return clean_projection


def _compute_theoretical_ctf(num_pixels, pixel_size, defocus, b_factor, amp):
    freq_1d = torch.fft.fftfreq(num_pixels, d=pixel_size)
    x, y = torch.meshgrid(freq_1d, freq_1d, indexing="ij")
    freq2 = x**2 + y**2
    freq = torch.sqrt(freq2)

    env = torch.exp(-b_factor * freq2 * 0.5)
    phase = defocus * torch.pi * 2.0 * 10000.0 * 0.019866

    ctf_2d = (
        -amp * torch.cos(phase * freq2 * 0.5)
        - torch.sqrt(torch.tensor(1.0 - amp**2)) * torch.sin(phase * freq2 * 0.5)
    )
    ctf_2d = ctf_2d * env / amp

    freq_np = freq.detach().cpu().numpy()
    ctf_np = ctf_2d.detach().cpu().numpy()

    # Radial averaging: this is the cleanest way to show a 1D theoretical CTF curve.
    r_max = float(freq_np.max())
    bins = np.linspace(0.0, r_max, max(64, num_pixels // 2))
    centers = 0.5 * (bins[:-1] + bins[1:])
    radial = np.zeros_like(centers)

    for i in range(len(centers)):
        mask = (freq_np >= bins[i]) & (freq_np < bins[i + 1])
        radial[i] = float(np.mean(ctf_np[mask])) if np.any(mask) else np.nan

    return ctf_np, centers, radial


@st.fragment
def render(instance_id: str = "main"):
    st.subheader("CTF Effect on Cat Projection (Simulation-Based)")
    st.write(
        "This widget generates a clean cat projection from the simulator, applies a CTF in Fourier space, "
        "and visualizes both the image effect and the theoretical transfer function."
    )

    try:
        simulator = load_simulator()
    except Exception as exc:
        st.error(str(exc))
        return

    def _k(name: str) -> str:
        return f"ctf_cat_{instance_id}_{name}"

    # Keep these controls explicitly movable across the intended teaching range.
    defocus_min, defocus_max = 0.5, 2.0
    b_min, b_max = 1.0, 100.0
    default_amp = float(np.clip(_as_scalar(simulator._config.get("AMP", 0.1), 0.1), 0.1, 1.5))

    default_defocus = float(np.clip(0.5, defocus_min, defocus_max))
    default_b = float(np.clip(12.0, b_min, b_max))

    ctf_presets = {
        "Config default": {
            "defocus": default_defocus,
            "b_factor": default_b,
            "amp": default_amp,
        },
        "Low-defocus, heavy damping": {"defocus": defocus_min, "b_factor": b_max, "amp": 0.10},
        "Balanced": {
            "defocus": float(np.clip(1.2, defocus_min, defocus_max)),
            "b_factor": float(np.clip(12.0, b_min, b_max)),
            "amp": 0.25,
        },
        "High-defocus, moderate damping": {
            "defocus": defocus_max,
            "b_factor": float(np.clip(20.0, b_min, b_max)),
            "amp": 0.50,
        },
        "High-defocus, low damping": {
            "defocus": defocus_max,
            "b_factor": float(np.clip(3.0, b_min, b_max)),
            "amp": 0.90,
        }
    }

    col1, col2, col3 = st.columns([1.0, 1.0, 1.15])

    with col1:
        st.markdown("### Controls")
        model_idx = st.slider(
            "Conformation Index",
            0,
            int(simulator.max_index),
            0,
            key=_k("model"),
        )
        rx = st.slider("Rotation X (deg)", -180, 180, 90, key=_k("rx"))
        ry = st.slider("Rotation Y (deg)", -180, 180, 90, key=_k("ry"))
        rz = st.slider("Rotation Z (deg)", -180, 180, 0, key=_k("rz"))

        preset_names = list(ctf_presets.keys())
        preset_name = st.selectbox("CTF Preset", options=preset_names, index=0, key=_k("preset_dropdown"))
        preset_vals = ctf_presets[preset_name]

        preset_track_key = _k("preset_track")
        if st.session_state.get(preset_track_key) != preset_name:
            st.session_state[_k("defocus")] = float(preset_vals["defocus"])
            st.session_state[_k("bfactor")] = float(preset_vals["b_factor"])
            st.session_state[_k("amp")] = float(preset_vals["amp"])
            st.session_state[preset_track_key] = preset_name

        with st.expander("Adjust CTF variables", expanded=False):
            st.slider(
                "Defocus",
                defocus_min,
                defocus_max,
                float(np.clip(st.session_state.get(_k("defocus"), default_defocus), defocus_min, defocus_max)),
                step=0.05,
                key=_k("defocus"),
            )

            st.slider(
                "B-factor",
                b_min,
                b_max,
                float(np.clip(st.session_state.get(_k("bfactor"), default_b), b_min, b_max)),
                step=0.5,
                key=_k("bfactor"),
            )

            st.slider(
                "Amplitude Contrast",
                0.1,
                0.99,
                default_amp,
                step=0.05,
                key=_k("amp"),
            )

        defocus = float(st.session_state[_k("defocus")])
        b_factor = float(st.session_state[_k("bfactor")])
        amp = float(st.session_state[_k("amp")])
        amp_model = min(amp, 0.99)
        
    with col3:
        st.markdown("### Theory CTF")
        

    clean_projection = _build_clean_cat_projection(simulator, model_idx, rx, ry, rz)

    defocus_t = torch.tensor([[defocus]], dtype=torch.float32)
    b_factor_t = torch.tensor([[b_factor]], dtype=torch.float32)
    amp_t = torch.tensor([[amp_model]], dtype=torch.float32)

    image_ctf = apply_ctf(
        clean_projection,
        defocus_t,
        b_factor_t,
        amp_t,
        simulator._pixel_size,
    )

    img_clean = clean_projection[0].detach().cpu().numpy()
    img_ctf = image_ctf[0].detach().cpu().numpy()

    num_pixels = int(simulator._num_pixels.item())
    pixel_size = float(simulator._pixel_size.item())
    ctf_2d, freq_1d, ctf_1d = _compute_theoretical_ctf(
        num_pixels=num_pixels,
        pixel_size=pixel_size,
        defocus=defocus,
        b_factor=b_factor,
        amp=amp_model,
    )

    with col2:
        st.markdown("### Projection Before & After CTF")
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        lo_clean = float(np.percentile(img_clean, 1))
        hi_clean = float(np.percentile(img_clean, 99))
        lo_ctf = float(np.percentile(img_ctf, 1))
        hi_ctf = float(np.percentile(img_ctf, 99))

        ax1.imshow(img_clean, cmap="gray", vmin=lo_clean, vmax=hi_clean, origin="lower", extent=[-1, 1, -1, 1])
        ax1.set_title("Original Cat Projection")
        ax1.axis("off")
        fig2, ax2 = plt.subplots(figsize=(4, 4))
        ax2.imshow(img_ctf, cmap="gray", vmin=lo_ctf, vmax=hi_ctf, origin="lower", extent=[-1, 1, -1, 1])
        ax2.set_title("Projection After CTF")
        ax2.axis("off")
        st.pyplot(fig1, clear_figure=True)
        st.pyplot(fig2, clear_figure=True)
        plt.close(fig1)
        plt.close(fig2)

    with col3:
        fig4, ax4 = plt.subplots(figsize=(6, 4), dpi=DISPLAY_DPI)
        ax4.plot(freq_1d, ctf_1d, color="#0f172a", linewidth=2)
        ax4.axhline(0.0, color="#64748b", linestyle="--", linewidth=1.2)
        ax4.set_title("Theoretical CTF Curve (Radial Average)")
        ax4.set_xlabel("Spatial Frequency")
        ax4.set_ylabel("CTF")
        ax4.grid(alpha=0.25)
        st.pyplot(fig4, clear_figure=True)
        plt.close(fig4)

        fig5, ax5 = plt.subplots(figsize=(6, 4), dpi=DISPLAY_DPI)
        ctf_vis = np.fft.fftshift(ctf_2d)
        im = ax5.imshow(ctf_vis, cmap="coolwarm", vmin=-1.0, vmax=1.0, interpolation=IMAGE_INTERPOLATION)
        ax5.set_title("2D CTF Transfer Function")
        ax5.axis("off")
        fig5.colorbar(im, ax=ax5, fraction=0.046, pad=0.04)
        st.pyplot(fig5, clear_figure=True)
        plt.close(fig5)

        st.caption("High resolution map of the theoretical form of a CTF.")

    st.divider()
    st.markdown("### Diagnostics")
    tab_diff, tab_fft = st.tabs(["Difference", "Fourier Power"])

    with tab_diff:
        diff_signed = img_ctf - img_clean
        diff_abs = np.abs(diff_signed)
        diff_col1, diff_col2 = st.columns(2)

        with diff_col1:
            fig_diff1, ax_diff1 = plt.subplots(figsize=(4.8, 4))
            vmax_signed = float(np.max(np.abs(diff_signed)) + 1e-12)
            ax_diff1.imshow(diff_signed, cmap="coolwarm", vmin=-vmax_signed, vmax=vmax_signed, origin="lower", extent=[-1, 1, -1, 1])
            ax_diff1.set_title("Signed Difference (CTF - Original)")
            ax_diff1.axis("off")
            st.pyplot(fig_diff1, clear_figure=True)
            plt.close(fig_diff1)

        with diff_col2:
            fig_diff2, ax_diff2 = plt.subplots(figsize=(4.8, 4))
            ax_diff2.imshow(diff_abs, cmap="inferno", origin="lower", extent=[-1, 1, -1, 1])
            ax_diff2.set_title("Absolute Difference |CTF - Original|")
            ax_diff2.axis("off")
            st.pyplot(fig_diff2, clear_figure=True)
            plt.close(fig_diff2)

        st.caption("Difference is computed as image_after_ctf - image_original on the same pixel grid.")

    with tab_fft:
        fft_clean = np.fft.fftshift(np.fft.fft2(img_clean))
        fft_ctf = np.fft.fftshift(np.fft.fft2(img_ctf))
        pow_clean = np.log(np.abs(fft_clean) + 1e-8)
        pow_ctf = np.log(np.abs(fft_ctf) + 1e-8)

        fig6, axes = plt.subplots(1, 2, figsize=(10, 4))
        vmin = float(np.percentile(pow_clean, 5))
        vmax = float(np.percentile(pow_clean, 99.5))

        axes[0].imshow(pow_clean, cmap="magma", vmin=vmin, vmax=vmax)
        axes[0].set_title("Original Fourier Power")
        axes[0].axis("off")

        axes[1].imshow(pow_ctf, cmap="magma", vmin=vmin, vmax=vmax)
        axes[1].set_title("CTF-Affected Fourier Power")
        axes[1].axis("off")

        plt.tight_layout()
        st.pyplot(fig6, clear_figure=True)
        plt.close(fig6)


if __name__ == "__main__":
    st.set_page_config(page_title="Cat CTF Widget", layout="wide")
    render(instance_id="standalone")
