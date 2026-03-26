import importlib.util
import os
import sys
from pathlib import Path

import streamlit as st


CHAPTER_DIR = Path(__file__).resolve().parent
APP_DIR = CHAPTER_DIR.parents[1]          # .../src/app
SRC_DIR = CHAPTER_DIR.parents[2]          # .../src

# Match main.py behavior so project imports (e.g., cryo_sbi) resolve in widgets.
sys.path.append(str(APP_DIR))
sys.path.append(str(SRC_DIR))


def render_markdown(filename: str) -> None:
    md_path = CHAPTER_DIR / filename
    if not md_path.exists():
        st.warning(f"Missing markdown file: {filename}")
        return

    with md_path.open("r", encoding="utf-8") as file:
        st.markdown(file.read())


def run_widget(widget_filename: str, function_name: str) -> None:
    widget_path = APP_DIR / "widgets" / widget_filename
    if not widget_path.exists():
        st.warning(f"Missing widget file: {widget_filename}")
        return

    module_name = f"chapter2_test_{widget_path.stem}"
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
    st.set_page_config(page_title="Chapter 2 Test App", layout="wide")

    st.title("Chapter 2 Test Flow")
    st.caption("Sequential test app for Chapter 2 markdown and widgets.")

    # Section 1: Waves, interference, Huygens, and far field.
    render_markdown("02_01_waves-and-diffraction.md")
    st.divider()
    run_widget("02_01_huygens.py", "single_wave")
    st.divider()
    render_markdown("02_02_multiple_waves.md")
    st.divider()
    run_widget("02_01_huygens.py", "huygens_fresnel_widget")
    st.divider()
    render_markdown("02_03_huygens.md")
    st.divider()
    run_widget("02_01_huygens.py", "multiple_sources_wave")
    st.divider()
    render_markdown("02_04_fraunhofer-bridge.md")
    st.divider()
    run_widget("02_02_fraunhofer.py", "fraunhofer_diffraction_widget")
    st.divider()

    # Section 2: Fourier progression from 1D to 2D to masking.
    render_markdown("02_03_fourier-intuition-1d-to-2d.md")
    st.divider()
    run_widget("02_03_1D-fourier-decomp.py", "render")
    st.divider()
    render_markdown("02_08_fourier-in-2d-images.md")
    st.divider()
    run_widget("02_04_2D-fourier-decomp.py", "render")
    st.divider()
    render_markdown("02_09_frequency-masking-to-ctf.md")
    st.divider()
    run_widget("02_05_masked-2d-fourier.py", "render")
    st.divider()

    # Section 3: Optical model, 3D geometry, transfer limits, and SPA.
    render_markdown("02_04_lenses-psf-ctf-image-formation.md")
    st.divider()
    render_markdown("02_05_ewald-and-projection-slice.md")
    st.divider()
    render_markdown("02_10_projection-slice-and-orientation-coverage.md")
    st.divider()
    render_markdown("02_06_ctf-in-real-cryoem-images.md")
    st.divider()
    render_markdown("02_07_spa-sample-prep-and-heterogeneity.md")


if __name__ == "__main__":
    main()
