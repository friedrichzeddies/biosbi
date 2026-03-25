import streamlit as st
import numpy as np
import torch
import os
import random
from scipy.spatial.transform import Rotation as R

from cryo_sbi.wpa_simulator.cryo_em_simulator import CryoEmSimulator, cryo_em_simulator
from cryo_sbi.wpa_simulator.image_generation import project_density

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "models", "2cat_large_batch_resnet")

@st.cache_resource
def load_simulator():
    sim_json = os.path.join(BASE_DIR, "simulation_parameters.json")
    if not os.path.exists(sim_json):
        return None
    simulator = CryoEmSimulator(sim_json, device="cpu")
    return simulator

def generate_projections(simulator, model_idx, rot_x, rot_y, rot_z):
    parameters = simulator._priors.sample((1,))
    idx_tensor = torch.tensor([[model_idx]], dtype=torch.float32)
    quat_tensor = torch.tensor([R.from_euler('xyz', [rot_x, rot_y, rot_z], degrees=True).as_quat()], dtype=torch.float32)
    
    batch_params = [
        idx_tensor, quat_tensor, 
        parameters[2], parameters[3], parameters[4], 
        parameters[5], parameters[6], parameters[7]
    ]
    
    noisy_img = cryo_em_simulator(
        simulator._models, 
        *batch_params, 
        simulator._num_pixels, 
        simulator._pixel_size
    )
    
    clean_img = project_density(
        simulator._models[[model_idx]], 
        quat_tensor, 
        parameters[2], 
        parameters[3], 
        simulator._num_pixels, 
        simulator._pixel_size
    )
    
    # Robust normalization to prevent outlier pixels turning the image black
    def robust_normalize(img_arr):
        vmin = np.percentile(img_arr, 1)
        vmax = np.percentile(img_arr, 99)
        clipped = np.clip(img_arr, vmin, vmax)
        if vmax > vmin:
            return (clipped - vmin) / (vmax - vmin)
        return np.zeros_like(clipped)
        
    clean_np = robust_normalize(clean_img.squeeze().detach().cpu().numpy())
    noisy_np = robust_normalize(noisy_img.squeeze().detach().cpu().numpy())
    
    # Convert to RGB [0.0, 1.0] valid for st.image
    noisy_rgb = np.stack((noisy_np,)*3, axis=-1)
    clean_rgb = np.stack((clean_np,)*3, axis=-1)
    
    return noisy_rgb, clean_rgb

def draw_border(img_rgb, color_rgb, thickness=3):
    img = img_rgb.copy()
    img[:thickness, :] = color_rgb
    img[-thickness:, :] = color_rgb
    img[:, :thickness] = color_rgb
    img[:, -thickness:] = color_rgb
    return img

@st.fragment
def render():
    st.markdown("""
        <style>
        .captcha-header {
            background-color: #4A90E2;
            color: white;
            padding: 15px;
            font-size: 20px;
            font-weight: bold;
            display: flex;
            align-items: center;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .captcha-title {
            font-size: 18px;
            margin-bottom: 10px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)
    
    simulator = load_simulator()
    if not simulator:
        st.error(f"Simulator parameters not found at {BASE_DIR}.")
        return

    # Initialize state variables safely
    if "quiz_round" not in st.session_state:
        st.session_state.quiz_round = 1
    if "r1_flipped" not in st.session_state:
        st.session_state.r1_flipped = False
    if "r1_choice" not in st.session_state:
        st.session_state.r1_choice = None
        
    # Round 2
    if "r2_models" not in st.session_state:
        st.session_state.r2_models = [random.choice([0, 1]) for _ in range(10)]
        st.session_state.r2_rots = [(random.uniform(0,360), random.uniform(0,360), random.uniform(0,360)) for _ in range(10)]
        st.session_state.r2_selected = [False]*10
        st.session_state.r2_verified = False
        
    # Round 3
    if "r3_models" not in st.session_state:
        st.session_state.r3_models = [random.choice([0, 1]) for _ in range(10)]
        st.session_state.r3_rots = [(random.uniform(0,360), random.uniform(0,360), random.uniform(0,360)) for _ in range(10)]
        st.session_state.r3_selected = [False]*10
        st.session_state.r3_verified = False

    st.markdown('<div class="captcha-title">Before you read this article, please complete the captcha:</div>', unsafe_allow_html=True)
    
    if st.session_state.quiz_round == 1:
        st.markdown('<div class="captcha-header">What is this cat doing?</div>', unsafe_allow_html=True)
        st.markdown("### Round 1: Let's start easy.")
        st.write("Is it standing or lying down?")
        
        _, clean_img = generate_projections(simulator, model_idx=0, rot_x=90, rot_y=90, rot_z=0)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(clean_img, use_container_width=True, caption="Clean Projection")
            
        if not st.session_state.r1_flipped:
            st.markdown("<div style='text-align: center; margin-top:20px;'>Select a card:</div>", unsafe_allow_html=True)
            bc1, bc2 = st.columns(2)
            if bc1.button("Standing", use_container_width=True):
                st.session_state.r1_choice = "standing"
                st.session_state.r1_flipped = True
                st.rerun()
            if bc2.button("Lying Down", use_container_width=True):
                st.session_state.r1_choice = "lying"
                st.session_state.r1_flipped = True
                st.rerun()
        else:
            if st.session_state.r1_choice == "standing":
                st.success("Correct! The model is clearly standing.")
            else:
                st.error("Not quite! This one is standing.")
                
            if st.button("Next Round", use_container_width=True, type="primary"):
                st.session_state.quiz_round = 2
                st.rerun()

    elif st.session_state.quiz_round == 2:
        st.markdown('<div class="captcha-header">Select all images where the cat is STANDING</div>', unsafe_allow_html=True)
        st.markdown("### Round 2: Clean Projections")
        st.write("These are random projections of the cat either lying down or standing up.")
        
        images = []
        for i in range(10):
            m = st.session_state.r2_models[i]
            r = st.session_state.r2_rots[i]
            _, c_img = generate_projections(simulator, m, *r)
            images.append(c_img)
        
        cols = st.columns(5)
        for i in range(10):
            col = cols[i % 5]
            with col:
                img_render = images[i]
                if st.session_state.r2_selected[i]:
                    img_render = draw_border(img_render, [0, 0, 1.0], thickness=4)
                if st.session_state.r2_verified:
                    if st.session_state.r2_models[i] == 0:
                        img_render = draw_border(img_render, [0, 1.0, 0], thickness=4)
                        
                st.image(img_render, use_container_width=True)
                
                if not st.session_state.r2_verified:
                    selected = st.checkbox("Select", key=f"r2_chk_{i}", label_visibility="collapsed")
                    if selected != st.session_state.r2_selected[i]:
                        st.session_state.r2_selected[i] = selected
                        st.rerun()
        
        if not st.session_state.r2_verified:
            if st.button("Verify", use_container_width=True, type="primary"):
                st.session_state.r2_verified = True
                st.rerun()
        else:
            correct_standing = sum(1 for i in range(10) if st.session_state.r2_selected[i] and st.session_state.r2_models[i] == 0)
            incorrect_standing = sum(1 for i in range(10) if st.session_state.r2_selected[i] and st.session_state.r2_models[i] == 1)
            total_standing = sum(1 for m in st.session_state.r2_models if m == 0)
            score = (correct_standing + (10 - total_standing - incorrect_standing)) / 10
            
            if score == 1.0:
                st.success("Perfect! You easily spotted them all. The green borders show the true standing cats.")
            elif score > 0.6:
                st.warning("Not entirely wrong! But you missed a few. It can be tricky from 2D projections.")
            else:
                st.error("Totally wrong! 3D orientations projected into 2D can be very misleading.")
                
            if st.button("Next Round", use_container_width=True, type="primary"):
                st.session_state.quiz_round = 3
                st.rerun()

    elif st.session_state.quiz_round == 3:
        st.markdown('<div class="captcha-header">Select all images where the cat is STANDING</div>', unsafe_allow_html=True)
        st.markdown("### Round 3: Parameterized Projections (Cryo-EM)")
        st.write("Now using full simulation parameters with noise and CTF. This will be quite hard.")
        
        images = []
        for i in range(10):
            m = st.session_state.r3_models[i]
            r = st.session_state.r3_rots[i]
            n_img, _ = generate_projections(simulator, m, *r)
            images.append(n_img)
        
        cols = st.columns(5)
        for i in range(10):
            col = cols[i % 5]
            with col:
                img_render = images[i]
                if st.session_state.r3_selected[i]:
                    img_render = draw_border(img_render, [0, 0, 1.0], thickness=4)
                if st.session_state.r3_verified:
                    if st.session_state.r3_models[i] == 0:
                        img_render = draw_border(img_render, [0, 1.0, 0], thickness=4)
                        
                st.image(img_render, use_container_width=True)
                
                if not st.session_state.r3_verified:
                    selected = st.checkbox("Select", key=f"r3_chk_{i}", label_visibility="collapsed")
                    if selected != st.session_state.r3_selected[i]:
                        st.session_state.r3_selected[i] = selected
                        st.rerun()
                        
        if not st.session_state.r3_verified:
            if st.button("Verify Captcha", use_container_width=True, type="primary"):
                st.session_state.r3_verified = True
                st.rerun()
        else:
            correct_standing = sum(1 for i in range(10) if st.session_state.r3_selected[i] and st.session_state.r3_models[i] == 0)
            incorrect_standing = sum(1 for i in range(10) if st.session_state.r3_selected[i] and st.session_state.r3_models[i] == 1)
            total_standing = sum(1 for m in st.session_state.r3_models if m == 0)
            score = (correct_standing + (10 - total_standing - incorrect_standing)) / 10
            
            if score == 1.0:
                st.success("Incredible! You spotted them all even through the noise. You are a Cryo-EM master.")
            elif score > 0.6:
                st.warning("Not bad! The noise makes it incredibly difficult. You got some right.")
            else:
                st.error("As expected, this is incredibly hard. Welcome to the ill-posed problem of pure 2D projection interference!")
            
            if st.button("Reset Captcha", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith("r1_") or key.startswith("r2_") or key.startswith("r3_") or key == "quiz_round":
                        del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="Cat Captcha", layout="wide")
    render()
