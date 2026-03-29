import sys
from pathlib import Path
import streamlit as st

from utils import render_markdown, run_widget

# Setup paths
APP_DIR = Path(__file__).resolve().parent
SRC_DIR = APP_DIR.parent
CONTENT_DIR = APP_DIR / "content"
CHAPTER2_DIR = CONTENT_DIR / "chapter_02"
CHAPTER3_DIR = CONTENT_DIR / "chapter_03"

sys.path.append(str(APP_DIR))
sys.path.append(str(SRC_DIR))

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
    /* Enhanced Sidebar ToC Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        font-size: 0.95rem;
    }
    
    section[data-testid="stSidebar"] .stMarkdown ul {
        list-style: none;
        padding-left: 0;
    }
    
    section[data-testid="stSidebar"] .stMarkdown li {
        margin: 0;
        padding: 0;
    }
    
    section[data-testid="stSidebar"] .stMarkdown a {
        text-decoration: none;
        color: #0d3b66;
        display: block;
        padding: 8px 12px;
        border-radius: 6px;
        transition: all 0.2s ease;
        font-weight: 500;
    }
    
    section[data-testid="stSidebar"] .stMarkdown a:hover {
        background-color: #e8f0f7;
        color: #ee6352;
        padding-left: 16px;
    }
    
    section[data-testid="stSidebar"] .stMarkdown strong a {
        font-size: 1.05rem;
        color: #0d3b66;
        padding: 10px 12px;
        margin-top: 6px;
        display: block;
    }
    
    section[data-testid="stSidebar"] .stMarkdown li ul li a {
        padding-left: 28px;
        font-size: 0.92rem;
        color: #444;
    }
    
    section[data-testid="stSidebar"] .stMarkdown li ul li a:hover {
        padding-left: 32px;
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
    
    st.sidebar.title("Navigation")
    
    # Hierarchical Sidebar Navigation (Markdown Links mapping to Anchor IDs)
    st.sidebar.markdown("""
- **[Intro](#intro)**
  - [Warm-up Quiz](#intro-quiz)

- **[Cryo-EM Image Formation](#cryo-em)**
  - [1.1 Waves & Diffraction](#waves-diffraction)
  - [Huygens Simulator](#huygens-simulator)
  - [Fraunhofer Diffraction](#fraunhofer-simulator)
  - [1.2 Fourier Intuition](#fourier-intuition)
  - [1D & 2D Fourier](#fourier-decomp)
  - [Fourier Manipulation](#fourier-manipulation)
  - [1.3 Imaging Geometry](#imaging-geometry)
  - [Ewald Sphere & Projection](#projection-slice)
  - [Lenses & CTF](#lenses-ctf)
  - [Full Simulation Pass](#full-simulation-pass)

- **[Simulation-Based Inference](#sbi)**
  - [2.1 SBI Foundations](#sbi-foundations)
  - [3D Embeddings](#sbi-embeddings)
  - [Experiment Inference](#experiment-inference)
  - [2.2 Misspecification](#misspecification)
  - [Validation Techniques](#validation-techniques)
  - [2.3 Simulation Calibration (SBC)](#sbc-calibration)
  - [Apply SBC](#sbc-own-data)

- **[Summary & Sources](#outro)**
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
    run_widget("03_01b_ill-posedness.py", "render_ui")
    
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
