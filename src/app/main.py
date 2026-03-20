import streamlit as st
import os
import sys

# Add the parent directory to Python path so we can import cryo_sbi if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from widgets.cat_projector import cat_projector_widget
from widgets.huygens import single_wave, huygens_fresnel_widget, multiple_sources_wave
from widgets.fraunhofer import fraunhofer_diffraction_widget

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
    
    # Run the interactive widget
    cat_projector_widget()

    st.divider()

    # run single and double wave animation
    single_wave()

    st.markdown("comments and hand-off to double")
    huygens_fresnel_widget()
    st.divider()

    # Multiple sources to explore planar waves
    multiple_sources_wave()
    st.divider()

    # Fraunhofer diffraction with double slit
    fraunhofer_diffraction_widget()
    st.divider()

if __name__ == "__main__":
    main()
