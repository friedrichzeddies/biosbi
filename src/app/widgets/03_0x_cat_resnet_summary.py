import json
import os
import sys

import matplotlib.pyplot as plt
import streamlit as st
import torch
from scipy.spatial.transform import Rotation

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import cryo_sbi.utils.estimator_utils as est_utils
from cryo_sbi.wpa_simulator.image_generation import project_density
from cryo_sbi.wpa_simulator.normalization import gaussian_normalize_image


SLIDER_KEYS = {
    "model_idx": "slider_0_model_idx",
    "rx": "slider_1_rx",
    "ry": "slider_2_ry",
    "rz": "slider_3_rz",
    "sigma": "slider_4_sigma",
    "shift_x": "slider_5_shift_x",
    "shift_y": "slider_6_shift_y",
}

SELECT_KEYS = {
    "estimator_model": "select_0_estimator_model",
}


def _slider_key(name: str, instance_id: str) -> str:
    return f"cat_resnet_{instance_id}_{SLIDER_KEYS[name]}"


def _select_key(name: str, instance_id: str) -> str:
    return f"cat_resnet_{instance_id}_{SELECT_KEYS[name]}"


def _embedding_grid_shape(dim: int) -> tuple[int, int]:
    """Return an exact rows x cols shape with rows as close as possible to sqrt(dim)."""
    side = int(dim ** 0.5)
    for rows in range(side, 0, -1):
        if dim % rows == 0:
            cols = dim // rows
            return rows, cols
    return 1, dim


def _embedding_to_image(embedding: torch.Tensor) -> torch.Tensor:
    dim = int(embedding.shape[0])
    rows, cols = _embedding_grid_shape(dim)
    return embedding.reshape(rows, cols)


def _get_scalar_or_mean(value) -> float:
    if isinstance(value, list):
        if len(value) == 0:
            return 0.0
        if len(value) == 1:
            return float(value[0])
        return float(0.5 * (value[0] + value[1]))
    return float(value)


def _get_bounds_or_default(value):
    if isinstance(value, list) and len(value) >= 2:
        lo = float(min(value[0], value[1]))
        hi = float(max(value[0], value[1]))
        return lo, hi
    scalar = _get_scalar_or_mean(value)
    return scalar, scalar


def _quat_wxyz_from_euler(rx: float, ry: float, rz: float) -> torch.Tensor:
    quat_xyzw = Rotation.from_euler("xyz", [rx, ry, rz], degrees=True).as_quat()
    return torch.tensor(
        [[quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]], dtype=torch.float32
    )


@st.cache_resource
def load_cat_resnet_assets(model_name: str):
    widget_dir = os.path.dirname(__file__)
    base_dir = os.path.abspath(os.path.join(widget_dir, "..", "data", "models", model_name))

    sim_cfg_path = os.path.join(base_dir, "simulation_parameters.json")
    train_cfg_path = os.path.join(base_dir, "training_parameters.json")
    estimator_path = os.path.join(base_dir, "estimator.pt")

    for fpath in (sim_cfg_path, train_cfg_path, estimator_path):
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Required file not found: {fpath}")

    with open(sim_cfg_path, "r", encoding="utf-8") as f:
        sim_cfg = json.load(f)

    model_file = sim_cfg.get("MODEL_FILE")
    if not model_file:
        raise ValueError("simulation_parameters.json is missing MODEL_FILE.")

    cat_model_path = model_file if os.path.isabs(model_file) else os.path.abspath(os.path.join(base_dir, model_file))
    if not os.path.exists(cat_model_path):
        raise FileNotFoundError(f"Cat model file from MODEL_FILE not found: {cat_model_path}")

    cat_models = torch.load(cat_model_path, map_location="cpu").to(torch.float32)
    if cat_models.ndim != 3 or cat_models.shape[1] != 3:
        raise ValueError("Cat model tensor must have shape (num_models, 3, num_atoms).")

    estimator = est_utils.load_estimator(train_cfg_path, estimator_path, device="cpu")

    sigma_lo, sigma_hi = _get_bounds_or_default(sim_cfg.get("SIGMA", 1.0))
    sigma_default = _get_scalar_or_mean(sim_cfg.get("SIGMA", 1.0))
    shift_default = _get_scalar_or_mean(sim_cfg.get("SHIFT", 0.0))

    # Precompute global vmin/vmax across all indexed conformations (identity rotation)
    num_models = cat_models.shape[0]
    all_quats = torch.tensor([[1.0, 0.0, 0.0, 0.0]], dtype=torch.float32).repeat(num_models, 1)
    all_sigmas = torch.tensor([sigma_default], dtype=torch.float32)
    all_shifts = torch.zeros((num_models, 2), dtype=torch.float32)

    with torch.no_grad():
        all_images = project_density(
            cat_models,
            all_quats,
            all_sigmas,
            all_shifts,
            torch.tensor(sim_cfg["N_PIXELS"], dtype=torch.float32),
            torch.tensor(sim_cfg["PIXEL_SIZE"], dtype=torch.float32),
        )
        all_images_normalized = gaussian_normalize_image(all_images)
        all_summaries = est_utils.compute_latent_repr(
            estimator=estimator,
            images=all_images_normalized,
            batch_size=num_models,
            device="cpu",
        )
        vmin = float(all_summaries.min())
        vmax = float(all_summaries.max())

    return {
        "cat_models": cat_models,
        "estimator": estimator,
        "num_pixels": torch.tensor(sim_cfg["N_PIXELS"], dtype=torch.float32),
        "pixel_size": torch.tensor(sim_cfg["PIXEL_SIZE"], dtype=torch.float32),
        "sigma_bounds": (sigma_lo, sigma_hi),
        "sigma_default": sigma_default,
        "shift_default": shift_default,
        "vmin": vmin,
        "vmax": vmax,
    }


def _get_available_estimator_models() -> list[str]:
    widget_dir = os.path.dirname(__file__)
    models_base_dir = os.path.abspath(os.path.join(widget_dir, "..", "data", "models"))
    if not os.path.exists(models_base_dir):
        return ["2cat_resnet"]

    available = [
        d
        for d in sorted(os.listdir(models_base_dir))
        if os.path.isdir(os.path.join(models_base_dir, d))
    ]
    return available if available else ["2cat_resnet"]


@st.fragment
def cat_resnet_summary_widget(instance_id: str = "main"):
    st.subheader("Cat Projection -> ResNet Summary")
    st.caption("Projection from cat model with cryo_sbi.project_density, then summary embedding via trained ResNet estimator.")

    available_models = _get_available_estimator_models()
    default_model = "2cat_resnet" if "2cat_resnet" in available_models else available_models[0]
    selected_model = st.selectbox(
        "Select Cached Estimator Model",
        options=available_models,
        index=available_models.index(default_model),
        key=_select_key("estimator_model", instance_id),
    )

    try:
        assets = load_cat_resnet_assets(selected_model)
    except Exception as exc:
        st.error(f"Could not load widget assets: {exc}")
        return

    cat_models = assets["cat_models"]
    estimator = assets["estimator"]

    controls_col, view_col = st.columns([1, 2])

    with controls_col:
        st.markdown("### Controls")
        model_idx = st.slider(
            "Model index",
            0,
            int(cat_models.shape[0] - 1),
            0,
            key=_slider_key("model_idx", instance_id),
        )
        rx = st.slider("Rotation X", -180, 180, 0, key=_slider_key("rx", instance_id))
        ry = st.slider("Rotation Y", -180, 180, 0, key=_slider_key("ry", instance_id))
        rz = st.slider("Rotation Z", -180, 180, 0, key=_slider_key("rz", instance_id))

        sigma_lo, sigma_hi = assets["sigma_bounds"]
        if sigma_hi > sigma_lo:
            sigma_val = st.slider(
                "Sigma",
                min_value=float(sigma_lo),
                max_value=float(sigma_hi),
                value=float(assets["sigma_default"]),
                step=0.01,
                key=_slider_key("sigma", instance_id),
            )
        else:
            sigma_val = float(assets["sigma_default"])
            st.write(f"Sigma: {sigma_val:.3f}")

        shift_default = float(assets["shift_default"])
        shift_x = st.slider(
            "Shift X",
            -5.0,
            5.0,
            value=shift_default,
            step=0.1,
            key=_slider_key("shift_x", instance_id),
        )
        shift_y = st.slider(
            "Shift Y",
            -5.0,
            5.0,
            value=shift_default,
            step=0.1,
            key=_slider_key("shift_y", instance_id),
        )

    coords = cat_models[model_idx : model_idx + 1]
    quat = _quat_wxyz_from_euler(rx, ry, rz)
    sigma = torch.tensor([sigma_val], dtype=torch.float32)
    shift = torch.tensor([[shift_x, shift_y]], dtype=torch.float32)

    image = project_density(
        coords,
        quat,
        sigma,
        shift,
        assets["num_pixels"],
        assets["pixel_size"],
    )

    # Keep the network input normalized similarly to training-time image scaling.
    image_for_summary = gaussian_normalize_image(image.clone())
    summary = est_utils.compute_latent_repr(
        estimator=estimator,
        images=image_for_summary,
        batch_size=1,
        device="cpu",
    )[0]

    image_np = image[0].detach().cpu().numpy()
    summary_np = summary.detach().cpu().numpy()

    with view_col:
        left, right = st.columns(2)

        with left:
            st.markdown("### Starting image")
            fig_img, ax_img = plt.subplots(figsize=(4, 4))
            ax_img.imshow(image_np, cmap="gray")
            ax_img.axis("off")
            st.pyplot(fig_img)
            plt.close(fig_img)

        with right:
            st.markdown("### ResNet summary")
            st.write(f"Embedding dimension: {summary_np.shape[0]}")
            summary_img = _embedding_to_image(summary)
            summary_img_np = summary_img.detach().cpu().numpy()
            st.write(f"Grid shape: {summary_img_np.shape[0]} x {summary_img_np.shape[1]} (no padding)")
            fig_sum, ax_sum = plt.subplots(figsize=(5, 4))
            im = ax_sum.imshow(
                summary_img_np,
                cmap="viridis",
                aspect="auto",
                vmin=assets["vmin"],
                vmax=assets["vmax"],
            )
            if summary_img_np.shape[0] == 1:
                ax_sum.set_xlabel("Feature index")
                ax_sum.set_ylabel("Row")
            else:
                ax_sum.set_xlabel("Embedding X")
                ax_sum.set_ylabel("Embedding Y")
            ax_sum.set_title("Summary embedding image")
            fig_sum.colorbar(im, ax=ax_sum, fraction=0.046, pad=0.04)
            st.pyplot(fig_sum)
            plt.close(fig_sum)
            
            if summary_np.shape[0] == 128:
                st.caption(
                    "Note: This 128-d embedding is shown as an 8x16 grid for readability only. "
                    "Cell neighborhood does not imply spatial structure or feature proximity."
                )


def render():
    cat_resnet_summary_widget(instance_id="render")


def _run_standalone():
    st.set_page_config(page_title="Cat ResNet Summary", layout="wide")
    render()


if __name__ == "__main__":
    _run_standalone()
