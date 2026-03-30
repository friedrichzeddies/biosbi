import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

@st.cache_resource
def generate_signal():
    """Generates a complex 1D signal comprised of 5 discrete sine-wave components."""
    N = 1000
    x = np.linspace(0, 4 * np.pi, N)
    freqs = np.array([1, 2, 3, 4, 5])
    
    # Generate random actual values
    amps = np.random.uniform(1.0, 5.0, size=5)
    amps[2] = 0.0  # Force middle amplitude to zero
    phases = np.random.uniform(-np.pi, np.pi, size=5)
    
    y_true = np.zeros_like(x)
    for f, A, phi in zip(freqs, amps, phases):
        y_true += A * np.sin(f * x + phi)
        
    return x, freqs, amps, phases, y_true

@st.fragment
def render():
    st.write("### 1D Fourier Decomposition")
    st.write("Visualize how combining simple sine waves (with distinct frequencies, amplitudes, and phases) can build entirely complex 1D signals.")
    
    x, freqs, true_amps, true_phases, y_true = generate_signal()
    
    # Initialize basic UI state
    if "decomp_active" not in st.session_state:
        st.session_state.decomp_active = False
        
    # Initialize component states only once per script load so memory is maintained across interactions
    for i in range(5):
        if f"amp_{i}" not in st.session_state:
            st.session_state[f"amp_{i}"] = float(true_amps[i])
        if f"phi_{i}" not in st.session_state:
            st.session_state[f"phi_{i}"] = float(true_phases[i])
        if f"toggle_{i}" not in st.session_state:
            st.session_state[f"toggle_{i}"] = False
            
    if "global_phase" not in st.session_state:
        st.session_state.global_phase = 0.0

    if st.session_state.decomp_active:
        st.write("#### Master Reconstruction Sum")
        
        # Toggles moved to master plot
        t_cols = st.columns(5)
        for i, c in enumerate(t_cols):
            with c:
                st.checkbox(f"Include Freq {freqs[i]}", key=f"toggle_{i}")
                
        # Global phase explicitly sits right under the master controls
        st.slider("Global Phase Shift (Spatial)", -float(np.pi), float(np.pi), value=0.0, key="global_phase")
        
        # Calculate current reconstructed state dynamically
        y_current = np.zeros_like(x)
        gp = st.session_state.global_phase
        for i in range(5):
            if st.session_state[f"toggle_{i}"]:
                f = freqs[i]
                A = st.session_state[f"amp_{i}"]
                phi = st.session_state[f"phi_{i}"]
                # Mathematical translation: shift x by gp so shape is preserved
                y_current += A * np.sin(f * (x + gp) + phi)
    else:
        # Before decomposition, the "current" signal is just the true signal
        y_current = y_true

    # Master Reconstruction Plot (Merged explicitly at the top)
    fig_main, ax_main = plt.subplots(figsize=(8, 2.8))
    
    if st.session_state.decomp_active:
        # Draw dotted line of truth
        ax_main.plot(x, y_true, color='grey', linestyle='--', label='True Original Signal', alpha=0.9, lw=3)
        # Draw solid line of current dynamic state
        ax_main.plot(x, y_current, color='#FF4B4B', linestyle='-', label='Reconstructed Overlap', lw=2)
        ax_main.legend(loc="upper right")
    else:
        # Initial visual of just the true complex signal
        ax_main.plot(x, y_true, 'k-', lw=2, label='True Original Signal')
        
    ax_main.margins(x=0)
    
    # Fix the Y-axis limits so optical scaling illusions don't incorrectly suggest amplitude changes
    max_y = np.max(np.abs(y_true)) * 1.5
    ax_main.set_ylim(-max_y, max_y)
    
    ax_main.axis('off')
    st.pyplot(fig_main, clear_figure=True, width="content")
    plt.close(fig_main)
    
    # Button to trigger decomposition
    if not st.session_state.decomp_active:
        st.write("---")
        if st.button("Calculate Fourier Decomposition", type="primary"):
            st.session_state.decomp_active = True
            st.rerun()
            
    # Draw interactive components if active
    if st.session_state.decomp_active:
        st.write("---")
        st.write("#### Discovered Fourier Components")
        
        cols = st.columns(5)
        for i, col in enumerate(cols):
            with col:
                st.write(f"**Frequency {freqs[i]}**")
                
                # Dynamic mini-plot
                A_curr = st.session_state[f"amp_{i}"]
                phi_curr = st.session_state[f"phi_{i}"]
                
                # To visualize component isolation without the global phase offset
                y_mini = A_curr * np.sin(freqs[i] * x + phi_curr)
                fig_mini, ax_mini = plt.subplots(figsize=(1.6, 1.2))
                ax_mini.plot(x, y_mini, color=f"C{i}", lw=2)
                ax_mini.set_ylim([-5.5, 5.5])
                ax_mini.margins(x=0)
                ax_mini.axis('off')
                st.pyplot(fig_mini, clear_figure=True, width="content")
                plt.close(fig_mini)
                
                # Interactive sliders bound to session state with explicit initial values
                st.slider("Amplitude", 0.0, 10.0, value=float(true_amps[i]), key=f"amp_{i}")
                st.slider("Phase", -float(np.pi), float(np.pi), value=float(true_phases[i]), key=f"phi_{i}")
                
                # Callback to reset individual component parameters exactly back to true values
                def reset_callback(idx=i):
                    st.session_state[f"amp_{idx}"] = float(true_amps[idx])
                    st.session_state[f"phi_{idx}"] = float(true_phases[idx])
                
                st.button("Reset To True", key=f"reset_{i}", on_click=reset_callback)

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
