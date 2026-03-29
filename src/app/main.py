import importlib.util
import os
import sys
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).resolve().parent  # .../src/app
SRC_DIR = APP_DIR.parent  # .../src
CONTENT_DIR = APP_DIR / "content"
CHAPTER2_DIR = CONTENT_DIR / "chapter_02"
CHAPTER3_DIR = CONTENT_DIR / "chapter_03"

# Match widget imports
sys.path.append(str(APP_DIR))
sys.path.append(str(SRC_DIR))


def render_markdown(filename: str, base_dir: Path = None) -> None:
    """Render markdown with image support. Images are detected via ![alt](path) syntax."""
    if base_dir is None:
        base_dir = CHAPTER2_DIR
    
    import re
    
    md_path = base_dir / filename
    if not md_path.exists():
        st.warning(f"Missing markdown file: {filename}")
        return

    with md_path.open("r", encoding="utf-8") as file:
        content = file.read()
    
    # Pattern to match markdown images: ![alt text](path/to/image.ext)
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    current_pos = 0
    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1)
        image_path_str = match.group(2)
        
        # Render text before image
        text_before = content[current_pos:match.start()].strip()
        if text_before:
            st.markdown(text_before)
        
        # Resolve image path
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
    
    # Render remaining text
    remaining_text = content[current_pos:].strip()
    if remaining_text:
        st.markdown(remaining_text)


def run_widget(widget_filename: str, function_name: str) -> None:
    """Dynamically load and run a widget."""
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


def main() -> None:
    st.set_page_config(page_title="biosbi - Learning Platform", layout="wide")

    st.title("biosbi: Cryo-EM & Simulation-Based Inference")
    st.caption("An interactive playground for understanding electron microscopy and simulation-based inference")
    
    render_markdown("01_intro.md", base_dir=CONTENT_DIR)
    st.divider()
    run_widget("01_intro-quiz.py", "render")
    st.divider()
    st.markdown("Below you find both core topics in two tabs. We strongly recommend you to _first_ " \
        "do the Cryo-EM bit, and then proceed with the SBI one.")
    cryo_tab, sbi_tab = st.tabs(["Cryo-EM", "SBI"])

    with cryo_tab:
        st.markdown("## Chapter 2: CryoEM Image Formation")

        # Section 1: Waves and diffraction
        render_markdown("02_01_waves-and-diffraction.md", base_dir=CHAPTER2_DIR)
        st.divider()
        run_widget("02_01_huygens.py", "single_wave")
        st.divider()
        render_markdown("02_02_multiple_waves.md", base_dir=CHAPTER2_DIR)
        run_widget("02_01_huygens.py", "huygens_fresnel_widget")
        run_widget("02_01_huygens.py", "multiple_sources_wave")
        st.divider()
        run_widget("02_02_fraunhofer.py", "fraunhofer_diffraction_widget")
        st.divider()

        # Section 2: Fourier intuition + decomposition
        render_markdown("02_05_fourier-intuition-1d-to-2d.md", base_dir=CHAPTER2_DIR)
        st.divider()
        run_widget("02_03_1D-fourier-decomp.py", "render")
        st.divider()
        run_widget("02_04_2D-fourier-decomp.py", "render")
        st.divider()
        render_markdown("02_06_fourier_manipulation.md", base_dir=CHAPTER2_DIR)
        st.divider()
        run_widget("02_06_cat_projector.py", "render")
        st.divider()
        render_markdown("02_06a_detour-and-fourier-manipulation.md", base_dir=CHAPTER2_DIR)
        st.divider()
        run_widget("02_05_masked-2d-fourier.py", "render")
        st.divider()
        render_markdown("02_07_manipulation2.md", base_dir=CHAPTER2_DIR)
        st.divider()

        # Section 3: Imaging geometry + transfer effects
        render_markdown("02_09_note.md", base_dir=CHAPTER2_DIR)

        with st.expander("Ewald sphere and projection-slice", expanded=False):
            render_markdown("02_10_ewald-and-projection-slice.md", base_dir=CHAPTER2_DIR)
            st.divider()
            run_widget("02_06_ewald-sphere.py", "render")
            st.divider()
            render_markdown("02_11_projection-slice-and-orientation-coverage.md", base_dir=CHAPTER2_DIR)
            st.divider()
            run_widget("02_07_projection-slice-theorem.py", "render")

        st.divider()
        render_markdown("02_12_lenses-psf-ctf-image-formation.md", base_dir=CHAPTER2_DIR)
        st.divider()
        run_widget("02_08_ctf-cat.py", "render")
        st.divider()
        render_markdown("02_13_ctf-in-real-cryoem-images.md", base_dir=CHAPTER2_DIR)
        st.divider()
        run_widget("02_09_full-simulation-pass.py", "render")
        st.divider()
        render_markdown("02_14_spa-sample-prep-and-heterogeneity.md", base_dir=CHAPTER2_DIR)

    with sbi_tab:
        st.markdown("## Chapter 3: Simulation-Based Inference")

        render_markdown("03_01_sbi-explainer.md", base_dir=CHAPTER3_DIR)
        st.divider()
        run_widget("03_0x_3d-cat.py", "render")
        st.divider()
        run_widget("03_01_cat_resnet_summary.py", "render")
        st.divider()
        render_markdown("03_02_NPE-explainer.md", base_dir=CHAPTER3_DIR)
        st.divider()
        run_widget("03_03_exp_inference.py", "render_ui")
        st.divider()
        render_markdown("03_03_model_misspec_general.md", base_dir=CHAPTER3_DIR)
        st.divider()

        with st.expander("Validation Techniques", expanded=False):
            run_widget("03_02_external_validation_umap.py", "render_ui")
            st.divider()
            run_widget("03_02_ill-posedness.py", "render_ui")
            st.divider()
            run_widget("03_03_external_validation_mmd.py", "render_ui")

        st.divider()
        render_markdown("03_04_sbc-theory.md", base_dir=CHAPTER3_DIR)
        st.divider()
        run_widget("03_04_simulation-based-calibration.py", "render")
        st.divider()
        render_markdown("03_05_sbc-own-data.md", base_dir=CHAPTER3_DIR)
        st.divider()
        run_widget("03_05_sbc_own_data.py", "render")

    st.divider()
    render_markdown("summary.md", base_dir=CONTENT_DIR)
    st.divider()
    render_markdown("sources.md", base_dir=CONTENT_DIR)


if __name__ == "__main__":
    main()
