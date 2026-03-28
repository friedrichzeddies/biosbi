import os

import matplotlib.pyplot as plt
import streamlit as st
import torch
from scipy.spatial.transform import Rotation

from cryo_sbi import CryoEmSimulator
from cryo_sbi.wpa_simulator.image_generation import project_density


BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "Chapter 2 - BioEM")

@st.cache_resource
def load_simulator():
    json_path = os.path.join(BASE_DIR, "cat_proj_params.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Missing simulation parameters: {json_path}")

    return CryoEmSimulator(json_path, device="cpu")


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


@st.fragment
def render(instance_id: str = "main"):
    st.subheader("Interactive Cat Projector")

    try:
        simulator = load_simulator()
    except Exception as exc:
        st.error(str(exc))
        return

    def _k(name: str) -> str:
        return f"cat_projector_{instance_id}_{name}"

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Euler Angles (degrees)")
        rx = st.slider("Rotation X", -180, 180, 0, key=_k("rx"))
        ry = st.slider("Rotation Y", -180, 180, 90, key=_k("ry"))
        rz = st.slider("Rotation Z", -180, 180, 90, key=_k("rz"))

    with col2:
        rot = Rotation.from_euler("xyz", [rx, ry, rz], degrees=True)
        quat_np = rot.as_quat()  # scipy returns [x, y, z, w]
        quat = torch.tensor(
            [[quat_np[3], quat_np[0], quat_np[1], quat_np[2]]],
            dtype=torch.float32,
        )

        sigma_val = _as_scalar(simulator._config.get("SIGMA", [1.0]), 1.0)
        shift_val = _as_scalar(simulator._config.get("SHIFT", 0.0), 0.0)
        sigma = torch.tensor([sigma_val], dtype=torch.float32)
        shift = torch.tensor([[shift_val, shift_val]], dtype=torch.float32)

        model_index = torch.tensor([[0.0]], dtype=torch.float32)
        models_selected = simulator._models[model_index.round().long().flatten()]

        clean_projection = project_density(
            models_selected,
            quat,
            sigma,
            shift,
            simulator._num_pixels,
            simulator._pixel_size,
        )

        img_data = clean_projection[0].detach().cpu().numpy()

        st.markdown("### Clean Projection")
        fig, ax = plt.subplots(figsize=(3.0, 3.0))
        ax.imshow(img_data, cmap="gray")
        ax.axis("off")
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)


def cat_projector_widget():
    """Backward-compatible alias used by older pages."""
    render(instance_id="legacy")


if __name__ == "__main__":
    st.set_page_config(page_title="Cat Projector", layout="wide")
    render(instance_id="standalone")
