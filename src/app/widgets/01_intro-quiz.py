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


def to_rgb(img_tensor):
    """Robustly normalize and convert a single-channel tensor image to RGB."""
    img_arr = img_tensor.squeeze().detach().cpu().numpy()
    vmin = np.percentile(img_arr, 1)
    vmax = np.percentile(img_arr, 99)
    clipped = np.clip(img_arr, vmin, vmax)
    if vmax > vmin:
        normalized = (clipped - vmin) / (vmax - vmin)
    else:
        normalized = np.zeros_like(clipped)
    return np.stack((normalized,) * 3, axis=-1)


def generate_round1_image(simulator, model_idx=0, rot_x=90, rot_y=90, rot_z=0):
    """Use fixed parameters so round 1 remains clear and deterministic."""
    device = simulator._models.device
    sigma_cfg = simulator._config["SIGMA"]
    sigma_value = float(sum(sigma_cfg) / len(sigma_cfg)) if isinstance(sigma_cfg, list) else float(sigma_cfg)

    quat_tensor = torch.tensor(
        [R.from_euler("xyz", [rot_x, rot_y, rot_z], degrees=True).as_quat()],
        dtype=torch.float32,
        device=device,
    )
    sigma_tensor = torch.tensor([[sigma_value]], dtype=torch.float32, device=device)
    shift_tensor = torch.zeros((1, 2), dtype=torch.float32, device=device)

    clean_img = project_density(
        simulator._models[[model_idx]],
        quat_tensor,
        sigma_tensor,
        shift_tensor,
        simulator._num_pixels,
        simulator._pixel_size,
    )

    return to_rgb(clean_img)

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
    
    noisy_rgb = to_rgb(noisy_img)
    clean_rgb = to_rgb(clean_img)
    
    return noisy_rgb, clean_rgb


def generate_round_images(simulator, models, rots, noisy=False):
    """Generate one fixed image per task and keep it stable across reruns."""
    images = []
    for model_idx, rot in zip(models, rots):
        noisy_img, clean_img = generate_projections(simulator, model_idx, *rot)
        images.append(noisy_img if noisy else clean_img)
    return images

def draw_border(img_rgb, color_rgb, thickness=3):
    img = img_rgb.copy()
    img[:thickness, :] = color_rgb
    img[-thickness:, :] = color_rgb
    img[:, :thickness] = color_rgb
    img[:, -thickness:] = color_rgb
    return img


def init_round_data(simulator, round_prefix, noisy):
    models_key = f"{round_prefix}_models"
    if models_key in st.session_state:
        return

    st.session_state[models_key] = [random.choice([0, 1]) for _ in range(10)]
    st.session_state[f"{round_prefix}_rots"] = [
        (random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360)) for _ in range(10)
    ]
    st.session_state[f"{round_prefix}_selected"] = [False] * 10
    st.session_state[f"{round_prefix}_verified"] = False
    st.session_state[f"{round_prefix}_images"] = generate_round_images(
        simulator,
        st.session_state[models_key],
        st.session_state[f"{round_prefix}_rots"],
        noisy=noisy,
    )
    for i in range(10):
        st.session_state[f"{round_prefix}_chk_{i}"] = False


def initialize_quiz_state(simulator):
    if "quiz_round" not in st.session_state:
        st.session_state.quiz_round = 1
    if "r1_flipped" not in st.session_state:
        st.session_state.r1_flipped = False
    if "r1_choice" not in st.session_state:
        st.session_state.r1_choice = None
    if "r1_image" not in st.session_state:
        st.session_state.r1_image = generate_round1_image(simulator, model_idx=0, rot_x=90, rot_y=90, rot_z=0)

    # Preload round 2 and 3 once so switching rounds feels immediate.
    init_round_data(simulator, round_prefix="r2", noisy=False)
    init_round_data(simulator, round_prefix="r3", noisy=True)


def move_to_round(round_number):
    st.session_state.quiz_round = round_number


def reset_quiz_state():
    for key in list(st.session_state.keys()):
        if key.startswith("r1_") or key.startswith("r2_") or key.startswith("r3_") or key == "quiz_round":
            del st.session_state[key]


def render_round2_or_3(round_prefix, verify_button_text):
    images = st.session_state[f"{round_prefix}_images"]

    if not st.session_state[f"{round_prefix}_verified"]:
        with st.form(f"{round_prefix}_selection_form", clear_on_submit=False):
            cols = st.columns(5)
            for i in range(10):
                col = cols[i % 5]
                with col:
                    st.image(images[i], use_container_width=True)
                    st.checkbox("Select", key=f"{round_prefix}_chk_{i}", label_visibility="collapsed")

            submitted = st.form_submit_button(verify_button_text, use_container_width=True, type="primary")

        if submitted:
            st.session_state[f"{round_prefix}_selected"] = [
                st.session_state.get(f"{round_prefix}_chk_{i}", False) for i in range(10)
            ]
            st.session_state[f"{round_prefix}_verified"] = True
    else:
        cols = st.columns(5)
        for i in range(10):
            col = cols[i % 5]
            with col:
                img_render = images[i]
                if st.session_state[f"{round_prefix}_selected"][i]:
                    img_render = draw_border(img_render, [0, 0, 1.0], thickness=4)
                if st.session_state[f"{round_prefix}_models"][i] == 0:
                    img_render = draw_border(img_render, [0, 1.0, 0], thickness=4)
                st.image(img_render, use_container_width=True)

        selected = st.session_state[f"{round_prefix}_selected"]
        models = st.session_state[f"{round_prefix}_models"]
        correct_standing = sum(1 for i in range(10) if selected[i] and models[i] == 0)
        incorrect_standing = sum(1 for i in range(10) if selected[i] and models[i] == 1)
        total_standing = sum(1 for m in models if m == 0)
        score = (correct_standing + (10 - total_standing - incorrect_standing)) / 10

        return score

    return None

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
        /* Remove Streamlit fade/transition effects for clearer captcha interaction */
        [data-testid="stImage"] img,
        [data-testid="stElementContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="stForm"] {
            animation: none !important;
            transition: none !important;
            opacity: 1 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    simulator = load_simulator()
    if not simulator:
        st.error(f"Simulator parameters not found at {BASE_DIR}.")
        return

    initialize_quiz_state(simulator)

    st.markdown('<div class="captcha-title">Before you read this article, please complete the captcha:</div>', unsafe_allow_html=True)

    st.radio(
        "Round",
        options=[1, 2, 3],
        key="quiz_round",
        horizontal=True,
        format_func=lambda r: f"Round {r}",
        label_visibility="collapsed",
    )
    
    if st.session_state.quiz_round == 1:
        st.markdown('<div class="captcha-header">What is this cat doing?</div>', unsafe_allow_html=True)
        st.markdown("### Round 1: Let's start easy.")
        st.write("Is it standing or lying down?")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(st.session_state.r1_image, use_container_width=True, caption="Clean Projection")
            
        if not st.session_state.r1_flipped:
            st.markdown("<div style='text-align: center; margin-top:20px;'>Select a card:</div>", unsafe_allow_html=True)
            bc1, bc2 = st.columns(2)
            choose_standing = bc1.button("Standing", use_container_width=True)
            choose_lying = bc2.button("Lying Down", use_container_width=True)

            if choose_standing or choose_lying:
                st.session_state.r1_choice = "standing" if choose_standing else "lying"
                st.session_state.r1_flipped = True

        if st.session_state.r1_flipped:
            if st.session_state.r1_choice == "standing":
                st.success("Correct! The model is clearly standing.")
            else:
                st.error("Not quite! This one is standing.")
                
            st.button(
                "Next Round",
                use_container_width=True,
                type="primary",
                on_click=move_to_round,
                args=(2,),
            )

    elif st.session_state.quiz_round == 2:
        st.markdown('<div class="captcha-header">Select all images where the cat is STANDING</div>', unsafe_allow_html=True)
        st.markdown("### Round 2: Clean Projections")
        st.write("These are random projections of the cat either lying down or standing up.")

        score = render_round2_or_3(round_prefix="r2", verify_button_text="Verify")
            
        if score is not None:
            if score == 1.0:
                st.success("Perfect! You easily spotted them all. The green borders show the true standing cats.")
            elif score > 0.6:
                st.warning("Not entirely wrong! But you missed a few. It can be tricky from 2D projections.")
            else:
                st.error("Totally wrong! 3D orientations projected into 2D can be very misleading.")
                
            st.button(
                "Next Round",
                use_container_width=True,
                type="primary",
                on_click=move_to_round,
                args=(3,),
            )

    elif st.session_state.quiz_round == 3:
        st.markdown('<div class="captcha-header">Select all images where the cat is STANDING</div>', unsafe_allow_html=True)
        st.markdown("### Round 3: Parameterized Projections (Cryo-EM)")
        st.write("Now using full simulation parameters with noise and CTF. This will be quite hard.")

        score = render_round2_or_3(round_prefix="r3", verify_button_text="Verify Captcha")
            
        if score is not None:
            if score == 1.0:
                st.success("Incredible! You spotted them all even through the noise. You are a Cryo-EM master.")
            elif score > 0.6:
                st.warning("Not bad! The noise makes it incredibly difficult. You got some right.")
            else:
                st.error("As expected, this is incredibly hard. Welcome to the ill-posed problem of pure 2D projection interference!")
            
            st.button("Reset Captcha", use_container_width=True, on_click=reset_quiz_state)

if __name__ == "__main__":
    st.set_page_config(page_title="Cat Captcha", layout="wide")
    render()
