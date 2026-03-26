import streamlit as st
import os
import sys
import importlib.util

# Add the parent directory to Python path so we can import cryo_sbi if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from widgets.huygens import single_wave, huygens_fresnel_widget, multiple_sources_wave
from widgets.fraunhofer import fraunhofer_diffraction_widget

def load_widget_file(filepath, func_name):
    abs_path = os.path.join(os.path.dirname(__file__), filepath)
    spec = importlib.util.spec_from_file_location("dynamic_widget", abs_path)
    module = importlib.util.module_from_spec(spec)
    # Prevent reloading issues in Streamlit
    sys.modules[filepath] = module
    spec.loader.exec_module(module)
    func = getattr(module, func_name)
    func()

def main():
    st.set_page_config(page_title="CryoSBI - Chapter 3: Inference & Validation", layout="wide")
    
    # Load intro text
    intro_path = os.path.join(os.path.dirname(__file__), "content", "03_0x_internal-validation-theory.md")
    if os.path.exists(intro_path):
        with open(intro_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.info("Validation theory content loaded from internal-validation-theory.md")

    st.divider()

    # --- Chapter 3: Inference and Validation ---
    
    st.header("3D Cat Model Visualization")
    load_widget_file("widgets/03_0x_3d-cat.py", "render")
    st.divider()

    st.header("Ill-Posedness in 2D Projections")
    load_widget_file("widgets/03_01_ill-posedness.py", "render_ui")
    st.divider()

    st.header("Full Posterior Inference Explorer")
    load_widget_file("widgets/03_exp_inference.py", "render_ui")
    st.divider()

    st.header("ResNet Latent Space Summary")
    load_widget_file("widgets/03_0x_cat_resnet_summary.py", "render")
    st.divider()

    st.header("External Validation: UMAP Embedding")
    load_widget_file("widgets/03_02_external_validation_umap.py", "render_ui")
    st.divider()

    st.header("External Validation: MMD Metrics")
    load_widget_file("widgets/03_03_external_validation_mmd.py", "render_ui")
    st.divider()

    st.header("SBC: Theoretical Calibration Check")
    load_widget_file("widgets/03_0x_simulation-based-calibration.py", "render")
    st.divider()

    st.header("SBC: Real-Data Conformation Calibration")
    load_widget_file("widgets/03_10_sbc_own_data.py", "render")
    st.divider()

if __name__ == "__main__":
    main()
