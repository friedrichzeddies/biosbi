import streamlit as st
import torch
import os
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation
from cryo_sbi import CryoEmSimulator
from cryo_sbi.wpa_simulator.image_generation import project_density

@st.cache_resource
def load_simulator():
    widget_dir = os.path.dirname(__file__)
    json_path = os.path.abspath(
        os.path.join(widget_dir, "..", "data", "Chapter 2 - BioEM", "cat_proj_params.json")
    )
    
    if not os.path.exists(json_path):
        st.error(f"Could not find simulation parameters at {json_path}")
        return None

    simulator = CryoEmSimulator(json_path)
    return simulator

@st.fragment
def cat_projector_widget():
    st.subheader("Interactive Cat Projector")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Euler Angles (degrees)")
        # Sliders for Euler angles
        rx = st.slider("Rotation X", -180, 180, 0)
        ry = st.slider("Rotation Y", -180, 180, 0)
        rz = st.slider("Rotation Z", -180, 180, 0)
        
    with col2:
        simulator = load_simulator()
        
        if simulator is not None:
            # Convert Euler to Quaternion using scipy.
            rot = Rotation.from_euler('xyz', [rx, ry, rz], degrees=True)
            quat_np = rot.as_quat()
            
            # wpa_simulator project_density expects [w, x, y, z] depending on the specific torch implementation
            # Since scipy outputs [x, y, z, w], we rearrange:
            quat = torch.tensor([[quat_np[3], quat_np[0], quat_np[1], quat_np[2]]], dtype=torch.float32)
            
            # The simulator pulls these directly from the config now
            num_pixels = simulator._num_pixels
            pixel_size = simulator._pixel_size
            
            # Use the first value of Sigma/Shift from priors or config
            sigma_val = simulator._config.get("SIGMA", [1.0])[0]
            sigma = torch.tensor([sigma_val], dtype=torch.float32)
            
            shift = torch.tensor([[simulator._config.get("SHIFT", 0.0), simulator._config.get("SHIFT", 0.0)]], dtype=torch.float32)
            
            # Generate the clean projection using cryo_sbi function directly on the simulator's pre-loaded models
            # We select model index 0 
            model_index = torch.tensor([[0.0]], dtype=torch.float32)
            models_selected = simulator._models[model_index.round().long().flatten()]
            
            clean_projection = project_density(
                models_selected,
                quat,
                sigma,
                shift,
                num_pixels,
                pixel_size
            )
            
            # Display the result
            img_data = clean_projection[0].detach().cpu().numpy()
            
            st.markdown("### Clean Projection")
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.imshow(img_data, cmap='gray')
            ax.axis('off')
            st.pyplot(fig)
