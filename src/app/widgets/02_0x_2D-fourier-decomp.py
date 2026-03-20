import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

@st.cache_resource
def generate_signal():
    """Generates a complex 2D signal comprised of 5 discrete 2D plane waves."""
    N = 100
    x = np.linspace(0, 1, N)
    y = np.linspace(0, 1, N)
    X, Y = np.meshgrid(x, y)
    
    # Define 2D spatial frequencies (u, v) to form a Crystallographic / Woven Lattice pattern
    freqs = [(2, 0), (0, 2), (2, 2), (2, -2), (4, 4)]
    
    # Intentionally crafted values to build a recognizable periodic structure:
    # 1. (2, 0) and (0, 2) at Amp=2 form a base grid of dots (an egg-carton).
    # 2. (2, 2) and (2, -2) at Amp=1 bridge the dots diagonally to create a woven/quilted look.
    # 3. (4, 4) at Amp=0.5 adds a sharp micro-dot strictly in the center of the lattice holes.
    amps = np.array([2.0, 2.0, 1.0, 1.0, 0.0])  # Component 5 (4, 4) starts dormant at 0.0
    
    # We use pi/2 to shift sines into cosines, ensuring they peak symmetrically at the origin
    phases = np.array([np.pi/2, np.pi/2, np.pi/2, np.pi/2, np.pi/2])
    
    Z_true = np.zeros_like(X)
    for (u, v), A, phi in zip(freqs, amps, phases):
        if A != 0.0:  # Z_true reflects the mathematically intended visible target
            Z_true += A * np.sin(2 * np.pi * (u * X + v * Y) + phi)
            
    # The true decomposition of this image correctly has the 5th frequency at 0.0!
    # Users can 'discover' its effect by sliding it manually, but mathematically 'Reset To True' handles it as 0.0
    return X, Y, freqs, amps, phases, Z_true

@st.fragment
def render():
    st.write("### 2D Fourier Decomposition")
    st.write("Visualize how combining simple 2D plane waves can build complex 2D images. This is the exact math underpinning true diffraction patterns!")
    
    X, Y, freqs, true_amps, true_phases, Z_true = generate_signal()
    
    # Initialize basic UI state for 2D component
    if "decomp_active_2d" not in st.session_state:
        st.session_state.decomp_active_2d = False
        
    # Initialize component states
    for i in range(5):
        if f"amp_2d_{i}" not in st.session_state:
            st.session_state[f"amp_2d_{i}"] = float(true_amps[i])
        if f"phi_2d_{i}" not in st.session_state:
            st.session_state[f"phi_2d_{i}"] = float(true_phases[i])
        if f"toggle_2d_{i}" not in st.session_state:
            st.session_state[f"toggle_2d_{i}"] = False
            
    if "gp_x" not in st.session_state:
        st.session_state.gp_x = 0.0
    if "gp_y" not in st.session_state:
        st.session_state.gp_y = 0.0

    if st.session_state.decomp_active_2d:
        st.write("#### Master Reconstruction Plot")
        
        # Toggles moved to master plot
        t_cols = st.columns(5)
        for i, c in enumerate(t_cols):
            with c:
                st.checkbox(f"Include {freqs[i]}", key=f"toggle_2d_{i}")
                
        # Global phase explicitly sits right under the master controls
        shift_col1, shift_col2 = st.columns(2)
        with shift_col1:
            st.slider("Global X Shift", -0.5, 0.5, value=0.0, key="gp_x")
        with shift_col2:
            st.slider("Global Y Shift", -0.5, 0.5, value=0.0, key="gp_y")
            
        # Calculate current reconstructed state dynamically
        Z_current = np.zeros_like(X)
        gx = st.session_state.gp_x
        gy = st.session_state.gp_y
        
        for i in range(5):
            if st.session_state[f"toggle_2d_{i}"]:
                u, v = freqs[i]
                A = st.session_state[f"amp_2d_{i}"]
                phi = st.session_state[f"phi_2d_{i}"]
                # Mathematical translation: shift X and Y individually so rigid 2D envelope shifts visually across frame
                Z_current += A * np.sin(2 * np.pi * (u * (X + gx) + v * (Y + gy)) + phi)
    else:
        # Before decomposition, the "current" signal is just the true signal
        Z_current = Z_true

    # Fix the Y-axis limits so optical scaling illusions don't incorrectly suggest amplitude changes
    max_z = np.max(np.abs(Z_true)) * 1.5

    # Master Reconstruction Plot
    if st.session_state.decomp_active_2d:
        fig_main, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # True Original
        im1 = ax1.imshow(Z_true, cmap='viridis', vmin=-max_z, vmax=max_z, origin='lower', extent=[0, 1, 0, 1])
        ax1.set_title("True Original Image")
        ax1.axis('off')
        
        # Reconstructed Overlap
        im2 = ax2.imshow(Z_current, cmap='viridis', vmin=-max_z, vmax=max_z, origin='lower', extent=[0, 1, 0, 1])
        ax2.set_title("Reconstructed Sum")
        ax2.axis('off')
        
        st.pyplot(fig_main, clear_figure=True)
    else:
        # Before hitting decomposition, just show a massive single original true signal
        fig_main, ax_main = plt.subplots(figsize=(6, 4))
        ax_main.imshow(Z_true, cmap='viridis', vmin=-max_z, vmax=max_z, origin='lower', extent=[0, 1, 0, 1])
        ax_main.set_title("True Original Image")
        ax_main.axis('off')
        st.pyplot(fig_main, clear_figure=True)
    
    # Button to trigger decomposition
    if not st.session_state.decomp_active_2d:
        st.write("---")
        if st.button("Calculate 2D Fourier Decomposition", type="primary", key="btn_2d_decomp"):
            st.session_state.decomp_active_2d = True
            st.rerun()
            
    # Draw interactive components if active
    if st.session_state.decomp_active_2d:
        st.write("---")
        st.write("#### Discovered Plane Waves")
        
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.write(f"**Freq (u,v): {freqs[i]}**")
                
                # Dynamic mini-plot
                u, v = freqs[i]
                A_curr = st.session_state[f"amp_2d_{i}"]
                phi_curr = st.session_state[f"phi_2d_{i}"]
                
                # To visualize isolated component without global spatial shifts
                Z_mini = A_curr * np.sin(2 * np.pi * (u * X + v * Y) + phi_curr)
                fig_mini, ax_mini = plt.subplots(figsize=(2, 2))
                ax_mini.imshow(Z_mini, cmap='viridis', vmin=-11, vmax=11, origin='lower', extent=[0, 1, 0, 1])
                ax_mini.axis('off')
                st.pyplot(fig_mini, clear_figure=True)
                
                # Interactive sliders bound to session state with explicit initial values
                st.slider("Amplitude", 0.0, 10.0, value=float(true_amps[i]), key=f"amp_2d_{i}")
                st.slider("Phase", -float(np.pi), float(np.pi), value=float(true_phases[i]), key=f"phi_2d_{i}")
                
                # Callback to reset individual component parameters exactly back to true values
                def reset_callback(idx=i):
                    st.session_state[f"amp_2d_{idx}"] = float(true_amps[idx])
                    st.session_state[f"phi_2d_{idx}"] = float(true_phases[idx])
                
                st.button("Reset To True", key=f"reset_2d_{i}", on_click=reset_callback)

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
