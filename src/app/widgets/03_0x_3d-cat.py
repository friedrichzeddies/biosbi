import os
import sys
import shutil
import streamlit as st
# Instead of buggy wrapper functions, import the raw frontend component and its state manager
from streamlit_stl import _component_func, stl_component

# Ensure src is in sys.path so we can import app modules gracefully
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

@st.cache_resource
def mount_stls_to_frontend():
    """
    Bypasses streamlit-stl's memory leak and FileNotFoundError bugs by directly copying
    the 10 precomputed STL files into the component's Streamlit static asset folder once.
    """
    data_dir = os.path.join(SCRIPT_DIR, "..", "data", "Chapter 3 - Inference", "cat_conformations")
    target_dir = stl_component.temp_folder
    
    for idx in range(1, 11):
        filename = f"cat_conformation_{idx:02d}.stl"
        src = os.path.join(data_dir, filename)
        dst = os.path.join(target_dir, filename)
        shutil.copy(src, dst)
    return True

@st.fragment
def render():
    """
    Renders the 3D viewer widget.
    Isolated fragment ensures slider interaction doesn't reload the entire app.
    """
    st.markdown("### 3D Cat Conformation Viewer")
    st.write("Explore different conformations of the 3D cat model used in the simulator.")
    
    # Mount files secretly into the component static server
    mount_stls_to_frontend()
    
    # Slider to select conformation (1 to 10)
    frame_idx = st.slider(
        "Select Conformation Frame", 
        min_value=1, 
        max_value=10, 
        value=1, 
        key="cat_conformation_slider"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Call the RAW component function directly, completely bypassing stl_from_text tempfile bugs
    _component_func(
        file_path=f"cat_conformation_{frame_idx:02d}.stl",
        color='#E74C3C',
        material='material',
        auto_rotate=False,
        opacity=1,
        shininess=0,
        cam_v_angle=60,
        cam_h_angle=-90,
        cam_distance=0,
        height=500,
        max_view_distance=1000,
        key="cat_3d_viewer_v3"
    )

# Allow standalone execution
if __name__ == "__main__":
    # Note: Streamlit throws an error if set_page_config is called multiple times.
    # It's only called here for testing the widget in isolation.
    st.set_page_config(page_title="3D Cat Viewer", layout="centered")
    render()
