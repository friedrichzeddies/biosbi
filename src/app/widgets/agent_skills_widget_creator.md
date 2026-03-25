# How to Program Streamlit Widgets

When building complex Streamlit applications with multiple interactive components (widgets), performance and modularity can become major bottlenecks. By default, any interaction in Streamlit—like moving a slider or clicking a button—triggers a top-to-bottom rerun of the entire script.

To circumvent this and build scalable apps, a highly effective design pattern is combining `@st.cache_resource` and `@st.fragment`.

## What does `@st.cache_resource` do?
**Mechanic:** It caches global, unserializable resources—such as deeply nested objects, Machine Learning models (PyTorch tensors/weights), database connections, or large dataset loaders (like `trimesh` geometry or GLB animation data). 

**Impact:** Streamlit normally clears local memory on every script rerun. By wrapping your heavy instantiation logic in `@st.cache_resource`, you guarantee it only computes and loads *once* upon the first execution. Further interactions will completely bypass the loading step, fetching the asset instantly from RAM.

## What does `@st.fragment` do?
**Mechanic:** It isolates a specific rendering function into its own localized execution environment (a "fragment"). 

**Impact:** If a user interacts with an input element (like a slider or a dropdown) that lives *inside* a function decorated with `@st.fragment`, **only that specific function reruns**. The rest of the main Streamlit application, including other widgets, remains completely untouched.

---

## Why this is the Ultimate Setup for Standalone Widgets

If you are building individual complex widgets (like a `cat_projector.py` tool) that will eventually be imported and glued together into one main dashboard file, this setup is perfect for several reasons:

### 1. Perfect Isolation (Zero Cross-Talk)
You can place 10 different widgets on the same page. If a user moves a slider in Widget A to rotate a molecule, only Widget A's `@st.fragment` executes. Widgets B through J don't recalculate, preventing annoying full-page flickering, losing scroll position, and massive computational overhead.

### 2. Self-Contained Modularity
Because each widget can define its own `@st.fragment` for its UI and its own `@st.cache_resource` for its specific underlying data, the widget becomes a pure "plug-and-play" module. 

You can simply `import my_widget` into the main file, and call `my_widget.render()`. The main file doesn't need to be polluted with state management, caching configuration, or complex logic. The widget encapsulates everything it needs to survive on its own.

### 3. Memory Efficiency
If multiple widgets on your dashboard happen to require the same underlying heavy asset (e.g. they all need to access the base physics engine), `@st.cache_resource` acts as a clever singleton. It ensures that regardless of which widget asks for the resource first, it is only loaded into the server's RAM exactly once, and then shared efficiently via reference.

### Summary Example
Here is what a perfect standalone widget looks like:

```python
import streamlit as st

# 1. Self-contained heavy memory management
@st.cache_resource
def load_heavy_data():
    return Engine("heavy_model.pt")

# 2. Self-contained UI and Logic execution
@st.fragment
def render_widget():
    # Grabs the cached data instantly (or loads it if it's the very first time)
    engine = load_heavy_data()
    
    st.write("### Interactive Cat Projector")
    
    # This interaction is trapped inside the fragment!
    angle = st.slider("Rotate", 0, 360, key="widget_a_slider")
    
    # 3. Execution isolated strictly to this widget
    img = engine.calculate_projection(angle)
    st.image(img)
```

When you glue this into `main.py`, the rest of your app has absolutely no idea how heavy this widget is—it just works flawlessly and independently.

> [!IMPORTANT] 
> **CRITICAL RULE**: Do not preemptively integrate widgets into `main.py` without being explicitly asked by the user! Always develop and test widgets in complete isolation.

---

## Agentic Implementation Patterns for cryo_sbi Widgets

When building widgets specifically for `biosbi` and `cryo_sbi`, follow these battle-tested patterns:

### 1. Loading Models and Posteriors
Use `@st.cache_resource` and construct strict absolute paths relative to `__file__` to avoid missing file errors when users run Streamlit from different working directories.
```python
import os
from cryo_sbi.wpa_simulator.cryo_em_simulator import CryoEmSimulator
import cryo_sbi.utils.estimator_utils as est_utils

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "models", "2cat_conv")

@st.cache_resource
def load_assets():
    sim_json = os.path.join(BASE_DIR, "simulation_parameters.json")
    train_json = os.path.join(BASE_DIR, "training_parameters.json")
    estimator_pt = os.path.join(BASE_DIR, "estimator.pt")
    
    simulator = CryoEmSimulator(sim_json, device="cpu")
    posterior = est_utils.load_estimator(train_json, estimator_pt, device="cpu")
    return simulator, posterior
```

### 2. Generating Clean and Noisy Projections
To manually generate a specific state (e.g., explicit 3D orientation and model index) rather than random sampling, tap directly into the backend `cryo_em_simulator` function and `project_density` for clean density visualization.
```python
from scipy.spatial.transform import Rotation as R
from cryo_sbi.wpa_simulator.cryo_em_simulator import cryo_em_simulator
from cryo_sbi.wpa_simulator.image_generation import project_density
import torch

def generate_projections(simulator, model_idx, rot_x, rot_y, rot_z):
    # Sample base parameters (CTF, SNR, shift, etc) from the JSON simulation prior
    parameters = simulator._priors.sample((1,))
    
    # Force the explicit model choices
    idx_tensor = torch.tensor([[model_idx]], dtype=torch.float32)
    quat_tensor = torch.tensor([R.from_euler('xyz', [rot_x, rot_y, rot_z], degrees=True).as_quat()], dtype=torch.float32)
    
    # Assemble the batch list perfectly matching the CryoEmSimulator signature
    batch_params = [
        idx_tensor, quat_tensor, 
        parameters[2], parameters[3], parameters[4], 
        parameters[5], parameters[6], parameters[7]
    ]
    
    # 1. Noisy Image (CTF applied, Noise applied)
    noisy_img = cryo_em_simulator(
        simulator._models, 
        *batch_params, 
        simulator._num_pixels, 
        simulator._pixel_size
    )
    
    # 2. Clean Image (Pure projected density)
    clean_img = project_density(
        simulator._models[[model_idx]], 
        quat_tensor, 
        parameters[2], 
        parameters[3], 
        simulator._num_pixels, 
        simulator._pixel_size
    )
    
    return noisy_img, clean_img
```

### 3. Sampling the Posterior (Dimension Safety)
Evaluating the SBI Inference model on images requires robust handling of the array indices, because Neural Posterior Estimators might predict 1 parameter (e.g. just Conformation Index) returning a 2D Array, or predict 5 parameters returning a 3D Array. Always use `.ndim` checks.
```python
images_batch = torch.cat([noisy_img_1, noisy_img_2], dim=0)

samples = est_utils.sample_posterior(
    estimator=posterior,
    images=images_batch,
    num_samples=1000,
    batch_size=1000,
    device="cpu"
)

# Extract Conformation Index securely (parameter 0)
if samples.ndim == 2:
    if samples.shape[0] == 2:   # (batch_size, num_samples)
        s1, s2 = samples[0, :], samples[1, :]
    else:                       # (num_samples, batch_size)
        s1, s2 = samples[:, 0], samples[:, 1]
else:
    if samples.shape[0] == 2:   # (batch_size, num_samples, params)
        s1, s2 = samples[0, :, 0], samples[1, :, 0]
    else:                       # (num_samples, batch_size, params)
        s1, s2 = samples[:, 0, 0], samples[:, 1, 0]

### 4. Safe Numerical 2D Fourier Transforms
When building widgets that manipulate or visualize the 2D Fourier space (Power Spectrum) of projections, standard numerical pitfalls must be handled robustly to prevent Streamlit crashes and ensure mathematical accuracy:

- **DC Component Centering:** Real-space images transformed via `np.fft.fft2` will place the zero-frequency (DC) component at the top-left `(0,0)`. You must use `np.fft.fftshift` to move it to the center of the array so radial (donut) masks can be applied intuitively.
- **Visualizing the Power Spectrum:** The raw complex amplitudes of FFT cover massive dynamic ranges. To visualize the Power Spectrum, use logarithmic scaling: `np.log(np.abs(fft_shifted) + 1e-8)`.
- **Applying Mathematical Masks:** Any frequency masks (e.g., boolean low-pass or high-pass donuts) must be applied to the raw complex `fft_shifted` array—*not* the log-scaled visualization array. 
- **Safe Inverse Transforms:** Before calling `np.fft.ifft2`, you must strictly undo the center shift via `np.fft.ifftshift(masked_fft)`. Finally, because of floating-point inaccuracies, the resulting inverse array will retain tiny imaginary numerical artifacts. You must discard them by taking strictly the real part via `np.real(inverse_fft)` before passing the image to `st.image()` or `matplotlib`, otherwise Streamlit will crash attempting to render a complex array.

```python
import numpy as np

# 1. Forward Transform & Shift
fft_complex = np.fft.fft2(clean_img_numpy)
fft_shifted = np.fft.fftshift(fft_complex)

# 2. Power Spectrum for Visualization
power_spectrum_vis = np.log(np.abs(fft_shifted) + 1e-8)

# 3. Apply Boolean Donut Mask
fft_shifted_masked = fft_shifted * my_boolean_mask

# 4. Safe Inverse Transform
fft_unshifted = np.fft.ifftshift(fft_shifted_masked)
img_filtered_complex = np.fft.ifft2(fft_unshifted)

# 5. Extract strictly the real part to prevent rendering crashes
img_filtered_safe = np.real(img_filtered_complex)
```

### 5. 1D Fourier Decomposition & Signal Reconstruction UI
When building highly interactive signal summation tools where users can tune individual signal components, keep these UI and mathematical patterns in mind:

- **Streamlit Slider Implicit Defaults:** If a slider uses a `key` bound to `st.session_state`, it generally remembers its state. However, on the *very first* script execution before that explicit line of slider code runs, Streamlit resets the visual slider element to its mathematical minimum. Always explicitly declare the `value=` parameter equal to your default starting variable to prevent sliders snapping to $0.0$ or $-pi$ on the very first mount.
  ```python
  st.slider("Phase", -np.pi, np.pi, value=true_phase, key=f"phi_{i}")
  ```

- **Matplotlib Y-Axis Optical Illusions:** When plotting the summation of dynamic sine waves, the mathematical peak amplitude will naturally grow and shrink based on constructive or destructive phase interference. However, `matplotlib` implicitly auto-scales the Y-axis constraints on every frame. This creates a terrible optical illusion where the signal looks like it is changing "vertical size" wildly or not changing at all when sliders move. Always lock the $Y$-limits strictly against the bounds of the true original target signal, so the visual representation of amplitude feels physically accurate.
  ```python
  max_height = np.max(np.abs(true_signal)) * 1.5
  ax.set_ylim(-max_height, max_height)
  ```

- **Mathematical Global Phase (Spatial vs Component):** Adding a "Global Phase" to a decomposed signal must be handled with care regarding user expectation:
  - Phase Shift Per Component: `y += A * sin(f * x + phi + global_phase)` mathematically applies an absolute phase angle to every wave. Visually, because the wavelengths are different (higher frequencies compress more waves into $2\pi$), this distorts the shape of the reconstructed packet itself and causes peaks to slide past each other dynamically.
  - Spatial Translation (Envelope Shift): `y += A * sin(f * (x + global_phase) + phi)` treats the global phase as a pure literal shift in the $x$ domain. This perfectly translates the *entire, rigidly assembled shape* of the complex wave left or right across the screen without dispersive distortion. Choose this method if users expect the shape to stay intact identically.
  - Spatial Translation (Envelope Shift): `y += A * sin(f * (x + global_phase) + phi)` treats the global phase as a pure literal shift in the $x$ domain. This perfectly translates the *entire, rigidly assembled shape* of the complex wave left or right across the screen without dispersive distortion. Choose this method if users expect the shape to stay intact identically.

### 6. Ill-Posedness & Arbitrary Conformation Inference UIs
When constructing inference dashboards (like `03_01_ill-posedness.py`) that must dynamically serve an arbitrary number of distinct 3D conformations (from 2 up to 100), follow these core agentic design patterns:

- **Graceful Simulator Fallbacks:** If a user selects a model directory that only contains `simulation_parameters.json` but no trained `estimator.pt`, the app should not crash. Use `os.path.exists` to verify the posterior files early. If they are missing, gracefully load the `CryoEmSimulator` anyway so the user can easily visualize all the dynamic simulation output images, and simply replace the KDE Inference plot block downstream with an `st.info()` warning them to run their training script first!
- **De-Quantization KDE Boundaries:** Normalizing flows predicting discrete integer classes (e.g. Conformation 0, 1, 2) often require the integer boundaries to be uniformly "de-quantized" with $\pm 0.5$ noise to be evaluated continuously. Because of this, the posterior scatter KDE plot (`sns.kdeplot`) will naturally leak into negative numbers like $-0.3$. You must explicitly set `ax.set_xlim(-0.5, num_models - 0.5)` and draw explicit vertical bounding dashed lines at `i - 0.5` so the user visually understands the uniform thresholds that mathematically round back down to the target integer states.
- **Weighted Percentage Histograms:** When pairing continuous KDE traces with discretized probability bar charts (`ax.hist()`), raw sample evaluation counts (e.g., 500 samples out of 1000) are unreadable for pure model probability assessment. You must dynamically cast the integer count into visually scaled percentages by injecting `weights=[np.ones_like(p) / len(p) * 100 for p in preds_list]` into the Matplotlib histogram baseline arguments.

### 7. Dynamic State-Based UI Explainers
When building mathematically heavy interactive apps, standard static text blocks are often insufficient to help the user connect the math to the visual intuition. Follow the "Red Thread" pattern: dynamically render explainer text boxes (`st.info`, `st.warning`, `st.error`) conditioned mathematically identically to the plots themselves.
- **Example Use Case:** If a user moves a slider that adjusts a Gaussian distribution's mean past a target point, the UI should explicitly spawn an `st.info()` block saying: *"Because you shifted the mean to the right of the target, the expected rank will rapidly decay... "*
- **Implementation:** Always evaluate the mathematical states (e.g., $Z$-score thresholds) and render matching text explicitly guiding the user on *why* the plot looks the way it does based purely on their current slider configurations.
