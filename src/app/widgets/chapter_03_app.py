import importlib.util
import os
import sys
from pathlib import Path

import streamlit as st

# Environment Setup
WIDGET_DIR = Path(__file__).resolve().parent
APP_DIR = WIDGET_DIR.parent                   # .../src/app
SRC_DIR = APP_DIR.parent                      # .../src
CONTENT_DIR = APP_DIR / "content" / "chapter_03"

# Match main.py behavior so project imports (e.g., cryo_sbi) resolve in widgets.
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))


def render_markdown(filename: str) -> None:
    md_path = CONTENT_DIR / filename
    if not md_path.exists():
        st.warning(f"Missing markdown file: {filename}")
        return

    with md_path.open("r", encoding="utf-8") as file:
        st.markdown(file.read())


def run_widget(widget_filename: str, function_name: str = "render") -> None:
    widget_path = WIDGET_DIR / widget_filename
    if not widget_path.exists():
        st.warning(f"Missing widget file: {widget_filename}")
        return

    module_name = f"chapter3_test_{widget_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, str(widget_path))
    if spec is None or spec.loader is None:
        st.error(f"Could not load widget: {widget_filename}")
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Note: If function_name is not found, we try 'render_ui' or 'render' as fallbacks
    func = getattr(module, function_name, None)
    if func is None:
        func = getattr(module, "render_ui", None)
    if func is None:
        func = getattr(module, "render", None)

    if func is None:
        st.error(f"Render function not found in {widget_filename}")
        return

    func()


def main() -> None:
    st.set_page_config(page_title="Chapter 3 Test App", layout="wide")

    st.title("Chapter 3: From Images to Conformations")
    st.caption("Sequential integrated flow for Chapter 3 theory and interactive validation.")

    # Section 1: The SBI Framework
    st.header("1. The SBI Framework")
    render_markdown("03_01_sbi-explainer.md")
    st.divider()
    
    st.subheader("Visualizing the Summary Network")
    st.info("How does a ResNet 'see' the projection data? The summary network extracts abstract features used for inference.")
    run_widget("03_01_cat_resnet_summary.py")
    st.divider()

    # Section 2: High-Fidelity Inference
    st.header("2. High-Fidelity Inference")
    render_markdown("03_02_NPE-explainer.md")
    st.divider()

    st.subheader("Ambiguity and Ill-Posedness")
    st.write("Before we infer, let's see why a single point estimate isn't enough.")
    run_widget("03_02_ill-posedness.py")
    st.divider()
    
    # Section 3: Internal & External Validation
    st.header("3. Internal & External Validation")
    render_markdown("03_03_model_misspec_general.md")
    st.divider()

    st.subheader("Interactive Inference Dashboard")
    run_widget("03_03_exp_inference.py")
    st.divider()

    
    with st.expander("🔬 View Dimensionality & Metric Sanity Checks", expanded=False):
        st.subheader("UMAP Embedding Sanity")
        run_widget("03_02_external_validation_umap.py")
        st.divider()
        st.subheader("MMD Statistical Distance")
        run_widget("03_03_external_validation_mmd.py")
    st.divider()

    # Section 4: Statistical Calibration (SBC)
    st.header("4. Statistical Calibration (SBC)")
    render_markdown("03_04_sbc-theory.md")
    st.divider()
    
    st.subheader("Idealized SBC Intuition")
    run_widget("03_04_simulation-based-calibration.py")
    st.divider()

    render_markdown("03_05_sbc-own-data.md")
    st.divider()
    
    st.subheader("SBC on Your Data")
    run_widget("03_05_sbc_own_data.py")


if __name__ == "__main__":
    main()
