import importlib.util
import os
import sys
from pathlib import Path
import re
import streamlit as st

# Setup paths
APP_DIR = Path(__file__).resolve().parent
SRC_DIR = APP_DIR.parent
CONTENT_DIR = APP_DIR / "content"
CHAPTER2_DIR = CONTENT_DIR / "chapter_02"
CHAPTER3_DIR = CONTENT_DIR / "chapter_03"

sys.path.append(str(APP_DIR))
sys.path.append(str(SRC_DIR))

def render_markdown(filename: str, base_dir: Path = None) -> None:
    if base_dir is None:
        base_dir = CHAPTER2_DIR
    
    md_path = base_dir / filename
    if not md_path.exists():
        st.warning(f"Missing markdown file: {filename}")
        return

    with md_path.open("r", encoding="utf-8") as file:
        content = file.read()
    
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    current_pos = 0
    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1)
        image_path_str = match.group(2)
        
        text_before = content[current_pos:match.start()].strip()
        if text_before:
            st.markdown(text_before)
        
        if image_path_str.startswith(('http://', 'https://')):
            image_path = image_path_str
        else:
            image_path = base_dir / image_path_str
            if not image_path.exists():
                st.warning(f"Image not found: {image_path}")
                continue
            image_path = str(image_path)
        
        st.image(image_path, caption=alt_text if alt_text else None)
        current_pos = match.end()
    
    remaining_text = content[current_pos:].strip()
    if remaining_text:
        st.markdown(remaining_text)


def run_widget(widget_filename: str, function_name: str) -> None:
    widget_path = APP_DIR / "widgets" / widget_filename
    if not widget_path.exists():
        st.warning(f"Missing widget file: {widget_filename}")
        return

    module_name = f"streamlit_widget_{widget_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, str(widget_path))
    if spec is None or spec.loader is None:
        st.error(f"Could not load widget: {widget_filename}")
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if not hasattr(module, function_name):
        st.error(f"Function '{function_name}' not found in {widget_filename}")
        return

    getattr(module, function_name)()


def inject_custom_css():
    st.markdown("""
    <style>
    .block-container { 
        max-width: 900px;
        padding-top: 3rem;
        padding-bottom: 5rem;
    }
    .stMarkdown p, .stMarkdown li { 
        font-size: 1.15rem; 
        line-height: 1.6;
    }
    /* Custom Sidebar ToC Styling */
    section[data-testid="stSidebar"] .stMarkdown a {
        text-decoration: none;
        color: inherit;
        display: block;
        padding: 4px 0;
    }
    section[data-testid="stSidebar"] .stMarkdown a:hover {
        color: #ff4b4b; /* Subtle hover color for toc links */
    }
    /* Simple anchor offset to avoid headers hiding behind sticky bars if any */
    .anchor-offset {
        scroll-margin-top: 6rem;
    }
    </style>
    """, unsafe_allow_html=True)


def anchor(id_string):
    """Injects a clean HTML anchor for the sidebar ToC links."""
    st.markdown(f"<div id='{id_string}' class='anchor-offset'></div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="biosbi | Educational Platform", layout="centered", initial_sidebar_state="expanded")
    inject_custom_css()
    
    st.sidebar.title("Table of Contents")
    
    # Hierarchical Sidebar Navigation (Markdown Links mapping to Anchor IDs)
    st.sidebar.markdown("""
- **[Intro](#intro)**
  - [Warm-up Quiz](#intro-quiz)
- **[Cryo-EM Image Formation](#cryo-em)**
  - [1.1 Waves & Diffraction](#waves-diffraction)
  - [Interactive: Huygens Simulator](#huygens-simulator)
  - [Interactive: Fraunhofer Diffraction](#fraunhofer-simulator)
  - [1.2 Fourier Intuition](#fourier-intuition)
  - [Interactive: 1D & 2D Fourier](#fourier-decomp)
  - [Interactive: Fourier Manipulation](#fourier-manipulation)
  - [1.3 Imaging Geometry](#imaging-geometry)
  - [Interactive: Ewald Sphere & Projection](#projection-slice)
  - [Interactive: Lenses & CTF](#lenses-ctf)
  - [Interactive: Full Simulation Pass](#full-simulation-pass)
- **[Simulation-Based Inference](#sbi)**
  - [2.1 SBI Foundations](#sbi-foundations)
  - [Interactive: 3D Embeddings](#sbi-embeddings)
  - [Interactive: Experiment Inference](#experiment-inference)
  - [2.2 Misspecification](#misspecification)
  - [Interactive: Validation Techniques](#validation-techniques)
  - [2.3 Simulation Calibration (SBC)](#sbc-calibration)
  - [Interactive: Apply SBC](#sbc-own-data)
- **[Outro](#outro)**
    """)

    # ==========================
    # MAIN CONTENT (Sequential)
    # ==========================

    anchor("intro")
    st.title("Welcome to biosbi")
    render_markdown("01_intro.md", base_dir=CONTENT_DIR)

    anchor("intro-quiz")
    st.markdown("### Interactive: Intuition Check")
    run_widget("01_intro-quiz.py", "render")
    
    st.divider()

    anchor("cryo-em")
    st.title("Chapter 1: Cryo-EM Image Formation")
    
    anchor("waves-diffraction")
    st.header("1.1 Waves & Diffraction")
    render_markdown("02_01_waves-and-diffraction.md", base_dir=CHAPTER2_DIR)
    run_widget("02_01_huygens.py", "single_wave")
    render_markdown("02_02_multiple_waves.md", base_dir=CHAPTER2_DIR)
    
    anchor("huygens-simulator")
    st.markdown("### Interactive: Huygens Simulator")
    run_widget("02_01_huygens.py", "huygens_fresnel_widget")
    run_widget("02_01_huygens.py", "multiple_sources_wave")
    
    anchor("fraunhofer-simulator")
    st.markdown("### Interactive: Fraunhofer Diffraction")
    run_widget("02_02_fraunhofer.py", "fraunhofer_diffraction_widget")

    st.divider()

    anchor("fourier-intuition")
    st.header("1.2 Fourier Intuition")
    render_markdown("02_05_fourier-intuition-1d-to-2d.md", base_dir=CHAPTER2_DIR)
    
    anchor("fourier-decomp")
    st.markdown("### Interactive: 1D & 2D Fourier")
    run_widget("02_03_1D-fourier-decomp.py", "render")
    run_widget("02_04_2D-fourier-decomp.py", "render")
    
    render_markdown("02_06_fourier_manipulation.md", base_dir=CHAPTER2_DIR)
    
    anchor("fourier-manipulation")
    st.markdown("### Interactive: Fourier Manipulation")
    run_widget("02_06_cat_projector.py", "render")
    render_markdown("02_06a_detour-and-fourier-manipulation.md", base_dir=CHAPTER2_DIR)
    run_widget("02_05_masked-2d-fourier.py", "render")
    render_markdown("02_07_manipulation2.md", base_dir=CHAPTER2_DIR)

    st.divider()

    anchor("imaging-geometry")
    st.header("1.3 Imaging Geometry")
    render_markdown("02_09_note.md", base_dir=CHAPTER2_DIR)
    
    with st.expander("Ewald Sphere & Projection-Slice Theorem", expanded=False):
        render_markdown("02_10_ewald-and-projection-slice.md", base_dir=CHAPTER2_DIR)
        
        anchor("projection-slice")
        st.markdown("### Interactive: Ewald Sphere")
        run_widget("02_06_ewald-sphere.py", "render")
        
        render_markdown("02_11_projection-slice-and-orientation-coverage.md", base_dir=CHAPTER2_DIR)
        st.markdown("### Interactive: Projection-Slice")
        run_widget("02_07_projection-slice-theorem.py", "render")
    
    render_markdown("02_12_lenses-psf-ctf-image-formation.md", base_dir=CHAPTER2_DIR)
    
    anchor("lenses-ctf")
    st.markdown("### Interactive: Lenses & CTF")
    run_widget("02_08_ctf-cat.py", "render")
    
    render_markdown("02_13_ctf-in-real-cryoem-images.md", base_dir=CHAPTER2_DIR)
    
    anchor("full-simulation-pass")
    st.markdown("### Interactive: Full Simulation Pass")
    run_widget("02_09_full-simulation-pass.py", "render")
    
    render_markdown("02_14_spa-sample-prep-and-heterogeneity.md", base_dir=CHAPTER2_DIR)

    st.divider()

    anchor("sbi")
    st.title("Chapter 2: Simulation-Based Inference")
    
    anchor("sbi-foundations")
    st.header("2.1 SBI Foundations")
    render_markdown("03_01_sbi-explainer.md", base_dir=CHAPTER3_DIR)
    render_markdown("03_02_NPE-explainer.md", base_dir=CHAPTER3_DIR)
    
    anchor("sbi-embeddings")
    st.markdown("### Interactive: Embeddings & Summaries")
    run_widget("03_0x_3d-cat.py", "render")
    run_widget("03_01_cat_resnet_summary.py", "render")
    
    anchor("experiment-inference")
    st.markdown("### Interactive: Experiment Inference")
    run_widget("03_03_exp_inference.py", "render_ui")

    st.divider()

    anchor("misspecification")
    st.header("2.2 Misspecification")
    render_markdown("03_03_model_misspec_general.md", base_dir=CHAPTER3_DIR)
    
    anchor("validation-techniques")
    st.markdown("### Interactive: Validation Techniques")
    with st.expander("Validation Tools", expanded=False):
        run_widget("03_02_external_validation_umap.py", "render_ui")
        run_widget("03_02_ill-posedness.py", "render_ui")
        run_widget("03_03_external_validation_mmd.py", "render_ui")

    st.divider()

    anchor("sbc-calibration")
    st.header("2.3 Simulation Calibration (SBC)")
    render_markdown("03_04_sbc-theory.md", base_dir=CHAPTER3_DIR)
    run_widget("03_04_simulation-based-calibration.py", "render")
    
    anchor("sbc-own-data")
    st.markdown("### Interactive: Apply SBC")
    render_markdown("03_05_sbc-own-data.md", base_dir=CHAPTER3_DIR)
    run_widget("03_05_sbc_own_data.py", "render")

    st.divider()

    anchor("outro")
    st.title("Summary & Sources")
    render_markdown("summary.md", base_dir=CONTENT_DIR)
    st.divider()
    render_markdown("sources.md", base_dir=CONTENT_DIR)


if __name__ == "__main__":
    main()
