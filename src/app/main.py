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
    st.set_page_config(page_title="CryoSBI Cat Projector", layout="wide")
    
    # Load intro text
    intro_path = os.path.join(os.path.dirname(__file__), "content/", "01_intro.md")
    if os.path.exists(intro_path):
        with open(intro_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.warning("intro.md not found.")
        
    st.divider()
    
    # 1. Huygens
    single_wave()
    st.markdown("comments and hand-off to double")
    huygens_fresnel_widget()
    multiple_sources_wave()
    st.divider()

    # 2. Fraunhofer
    fraunhofer_diffraction_widget()
    st.divider()
    
    # 3. 1D Fourier Decomposition
    load_widget_file("widgets/02_0x_1D-fourier-decomp.py", "render")
    st.divider()
    
    # 4. 2D Fourier Decomposition
    load_widget_file("widgets/02_0x_2D-fourier-decomp.py", "render")
    st.divider()
    
    # 5. Masked 2D Fourier
    load_widget_file("widgets/02_0x_masked-2d-fourier.py", "render")
    st.divider()
    
    # 6. Ill-Posedness Conformations
    load_widget_file("widgets/03_01_ill-posedness.py", "render_ui")
    st.divider()

if __name__ == "__main__":
    main()
