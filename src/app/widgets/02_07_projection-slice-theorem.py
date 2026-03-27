import numpy as np
import matplotlib.pyplot as plt
import streamlit as st


PLOT_STYLE = {
    "figure.dpi": 140,
    "axes.titlesize": 11,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.grid": True,
    "grid.alpha": 0.2,
    "grid.linestyle": "--",
}


def _apply_plot_style() -> None:
    plt.rcParams.update(PLOT_STYLE)


def _angles_requested(num_angles: int) -> np.ndarray:
    return np.linspace(0.0, 180.0, int(num_angles), endpoint=False)


def _effective_unique_angles(num_angles: int, size: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Quantize angle directions to the pixel grid to estimate how many distinct
    Fourier rays are actually represented at finite resolution.
    """
    angles = _angles_requested(num_angles)
    center = size // 2
    signatures = []
    for angle in angles:
        theta = np.deg2rad(angle)
        endpoint = (
            center + int(np.round((center - 1) * np.cos(theta))),
            center + int(np.round((center - 1) * np.sin(theta))),
        )
        signatures.append(endpoint)

    signatures = np.array(signatures, dtype=int)
    _, unique_idx = np.unique(signatures, axis=0, return_index=True)
    unique_idx = np.sort(unique_idx)
    return angles, angles[unique_idx]


@st.cache_resource
def _build_phantom(size: int = 96) -> dict:
    x = np.linspace(-1.0, 1.0, size)
    y = np.linspace(-1.0, 1.0, size)
    xx, yy = np.meshgrid(x, y, indexing="xy")

    phantom = (
        1.4 * np.exp(-(((xx + 0.30) / 0.20) ** 2 + ((yy + 0.10) / 0.30) ** 2))
        + 0.8 * np.exp(-(((xx - 0.25) / 0.18) ** 2 + ((yy - 0.25) / 0.15) ** 2))
        + 0.6 * np.exp(-(((xx - 0.10) / 0.10) ** 2 + ((yy + 0.35) / 0.22) ** 2))
    )

    phantom = phantom / np.max(phantom)

    dx = x[1] - x[0]
    freq = np.fft.fftshift(np.fft.fftfreq(size, d=dx))
    f2 = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(phantom)))

    return {
        "image": phantom,
        "x": x,
        "y": y,
        "freq": freq,
        "fft2": f2,
    }



def _bilinear_sample_grid(arr: np.ndarray, axis: np.ndarray, xq: np.ndarray, yq: np.ndarray) -> np.ndarray:
    n = arr.shape[0]
    amin = axis[0]
    step = axis[1] - axis[0]

    ix = (xq - amin) / step
    iy = (yq - amin) / step

    valid = (ix >= -0.5) & (ix <= n - 0.5) & (iy >= -0.5) & (iy <= n - 0.5)

    ix0 = np.floor(ix).astype(int)
    iy0 = np.floor(iy).astype(int)
    ix1 = np.clip(ix0 + 1, 0, n - 1)
    iy1 = np.clip(iy0 + 1, 0, n - 1)
    ix0 = np.clip(ix0, 0, n - 1)
    iy0 = np.clip(iy0, 0, n - 1)

    wx = ix - ix0
    wy = iy - iy0

    wx = np.maximum(0, np.minimum(1, wx))
    wy = np.maximum(0, np.minimum(1, wy))

    v00 = arr[iy0, ix0]
    v10 = arr[iy0, ix1]
    v01 = arr[iy1, ix0]
    v11 = arr[iy1, ix1]

    sampled = (
        (1.0 - wx) * (1.0 - wy) * v00
        + wx * (1.0 - wy) * v10
        + (1.0 - wx) * wy * v01
        + wx * wy * v11
    )

    sampled[~valid] = 0.0
    return sampled


def _compute_projection(image: np.ndarray, x_axis: np.ndarray, theta_deg: float) -> tuple:
    theta = np.deg2rad(theta_deg)
    u = np.array([np.cos(theta), np.sin(theta)])
    v = np.array([-np.sin(theta), np.cos(theta)])

    extent = x_axis[-1] - x_axis[0]
    t = np.linspace(-extent / 2.0, extent / 2.0, image.shape[0])
    s_vals = np.linspace(-extent / 1.4, extent / 1.4, 180)

    tt, ss = np.meshgrid(t, s_vals, indexing="xy")
    xq = tt * u[0] + ss * v[0]
    yq = tt * u[1] + ss * v[1]

    sampled = _bilinear_sample_grid(image, x_axis, xq, yq)
    projection = np.trapezoid(sampled, s_vals, axis=0)

    return t, projection



def _fft_projection(projection: np.ndarray, t_axis: np.ndarray) -> tuple:
    dt = t_axis[1] - t_axis[0]
    freq = np.fft.fftshift(np.fft.fftfreq(projection.size, d=dt))
    proj_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(projection)))
    return freq, proj_fft


def _extract_central_slice(fft2: np.ndarray, freq_axis: np.ndarray, freq_line: np.ndarray, theta_deg: float) -> np.ndarray:
    theta = np.deg2rad(theta_deg)
    kx = freq_line * np.cos(theta)
    ky = freq_line * np.sin(theta)
    return _bilinear_sample_grid(fft2, freq_axis, kx, ky)


def _build_sparse_fft_from_angles(
    image: np.ndarray, x_axis: np.ndarray, freq_axis: np.ndarray, num_angles: int
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build a sparse 2D FFT by extracting central slices from projections at multiple angles.
    This simulates the tomographic sampling problem.
    """
    size = len(freq_axis)
    accum_fft = np.zeros((size, size), dtype=complex)
    hit_count = np.zeros((size, size), dtype=float)
    step = freq_axis[1] - freq_axis[0]
    
    _, angles = _effective_unique_angles(num_angles, size)
    
    for angle in angles:
        # Compute projection at this angle
        t_axis, projection = _compute_projection(image, x_axis, angle)
        
        # Get its 1D FFT
        freq_line, proj_fft = _fft_projection(projection, t_axis)
        
        # Extract the central slice at this angle and accumulate in sparse 2D FFT grid.
        # Multiple angles can map to the same pixel, so average later.
        theta = np.deg2rad(angle)
        kx = freq_line * np.cos(theta)
        ky = freq_line * np.sin(theta)

        for kx_val, ky_val, fft_val in zip(kx, ky, proj_fft):
            ix = int(np.round((kx_val - freq_axis[0]) / step))
            iy = int(np.round((ky_val - freq_axis[0]) / step))
            
            if 0 <= ix < size and 0 <= iy < size:
                accum_fft[iy, ix] += fft_val
                hit_count[iy, ix] += 1.0

    sparse_fft = np.zeros_like(accum_fft)
    valid = hit_count > 0
    sparse_fft[valid] = accum_fft[valid] / hit_count[valid]
    return sparse_fft, hit_count


def _reconstruct_from_sparse_slices(sparse_fft: np.ndarray, hit_count: np.ndarray) -> np.ndarray:
    """
    Reconstruct by inverse FFT using only the actually sampled frequency pixels.
    Unsampled frequencies are explicitly set to zero.
    """
    sampled_fft = np.zeros_like(sparse_fft)
    sampled_fft[hit_count > 0] = sparse_fft[hit_count > 0]

    # One inverse FFT turns the sparse frequency grid back into a real-space image.
    reconstructed = np.real(np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(sampled_fft))))

    # Normalize to display scale; without this, amplitude can be tiny even with valid structure.
    reconstructed = reconstructed - reconstructed.min()
    max_val = reconstructed.max()
    if max_val > 0:
        reconstructed = reconstructed / max_val

    return np.clip(reconstructed, 0.0, 1.0)


def _frequency_coverage_density(freq_axis: np.ndarray, num_angles: int) -> np.ndarray:
    """
    Compute the density of angle slices hitting each frequency pixel.
    Shows how low frequencies have redundant coverage while high frequencies are sparse.
    """
    size = len(freq_axis)
    coverage = np.zeros((size, size))
    _, angles = _effective_unique_angles(num_angles, size)
    center = size // 2
    freq_line = freq_axis
    step = freq_axis[1] - freq_axis[0]
    
    for angle in angles:
        theta = np.deg2rad(angle)
        for f in freq_line:
            x_idx = int(np.round(center + (f * np.cos(theta)) / step))
            y_idx = int(np.round(center + (f * np.sin(theta)) / step))
            if 0 <= x_idx < size and 0 <= y_idx < size:
                coverage[y_idx, x_idx] += 1
    
    return coverage


def _plot_forward_stage(data: dict, theta_deg: float) -> tuple[plt.Figure, plt.Figure, plt.Figure]:
    """
    STAGE 1: Single projection anatomy
    Shows object → projection → its Fourier transform.
    """
    _apply_plot_style()
    t_axis, projection = _compute_projection(data["image"], data["x"], theta_deg)
    freq_line, proj_fft = _fft_projection(projection, t_axis)

    # Plot 1: Object with projection direction
    fig1 = plt.figure(figsize=(5.8, 5.0))
    ax1 = fig1.add_subplot(1, 1, 1)
    ax1.imshow(data["image"], cmap="gray", origin="lower", extent=[-1, 1, -1, 1])
    theta_rad = np.deg2rad(theta_deg)
    u = np.array([np.cos(theta_rad), np.sin(theta_rad)])
    arrow_scale = 0.4
    ax1.arrow(-arrow_scale * u[0], -arrow_scale * u[1],
              2 * arrow_scale * u[0], 2 * arrow_scale * u[1],
              head_width=0.08, head_length=0.12, fc="#ff7f0e", ec="#ff7f0e", alpha=0.7, linewidth=1.0)
    ax1.set_title("Object and projection direction")
    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.grid(alpha=0.1, color="white")
    fig1.tight_layout()

    # Plot 2: The 1D projection
    fig2 = plt.figure(figsize=(5.8, 4.8))
    ax2 = fig2.add_subplot(1, 1, 1)
    ax2.plot(t_axis, projection, color="#1f77b4", linewidth=2.4)
    ax2.fill_between(t_axis, 0, projection, alpha=0.3, color="#1f77b4")
    ax2.set_title(r"Projection $p_\theta(t)$ (line integral)")
    ax2.set_xlabel("detector coordinate t")
    ax2.set_ylabel("intensity")
    ax2.grid(alpha=0.2)
    fig2.tight_layout()

    # Plot 3: FFT of the projection
    fig3 = plt.figure(figsize=(5.8, 4.8))
    ax3 = fig3.add_subplot(1, 1, 1)
    ax3.plot(freq_line, np.abs(proj_fft), color="#ef4444", linewidth=2.2)
    ax3.fill_between(freq_line, 0, np.abs(proj_fft), alpha=0.25, color="#ef4444")
    ax3.set_title(r"Fourier spectrum $|\mathcal{F}\{p_\theta\}|$")
    ax3.set_xlabel("frequency")
    ax3.set_ylabel("magnitude")
    ax3.grid(alpha=0.2)
    fig3.tight_layout()

    return fig1, fig2, fig3


def _plot_reconstruction_stage(
    data: dict, sparse_fft: np.ndarray, recon_clipped: np.ndarray, show_overlay: bool = False
) -> tuple[plt.Figure, plt.Figure, plt.Figure]:
    """
    STAGE 2: Reconstruction anatomy (3-column layout)
    Shows sparse FFT slices from projections, reconstructed object, and absolute error vs original.
    """
    _apply_plot_style()
    error_map = np.abs(data["image"] - recon_clipped)

    # Plot 1: Sparse 2D FFT from projections
    fig1 = plt.figure(figsize=(5.8, 5.0))
    ax1 = fig1.add_subplot(1, 1, 1)
    sparse_mag = np.log(np.abs(sparse_fft) + 1e-8)
    ax1.imshow(sparse_mag, cmap="magma", origin="lower")
    ax1.set_title("Many, but not all, Fourier slices")
    ax1.set_xlabel("kx")
    ax1.set_ylabel("ky")
    ax1.set_xticks([])
    ax1.set_yticks([])
    fig1.tight_layout()

    # Plot 2: Reconstruction (optionally with original overlay)
    fig2 = plt.figure(figsize=(5.8, 5.0))
    ax2 = fig2.add_subplot(1, 1, 1)
    ax2.imshow(recon_clipped, cmap="gray", origin="lower", extent=[-1, 1, -1, 1], vmin=0, vmax=1)
    if show_overlay:
        orig = data["image"]
        orig_masked = np.ma.masked_where(orig < orig.max() * 0.1, orig)
        ax2.imshow(orig_masked, cmap="hot", origin="lower", extent=[-1, 1, -1, 1], alpha=0.45)
        ax2.set_title("Reconstruction (hot overlay: original)")
    else:
        ax2.set_title("Reconstruction")
    ax2.axis("off")
    fig2.tight_layout()

    # Plot 3: Absolute error vs original
    fig3 = plt.figure(figsize=(5.8, 5.0))
    ax3 = fig3.add_subplot(1, 1, 1)
    im_err = ax3.imshow(error_map, cmap="hot", origin="lower", extent=[-1, 1, -1, 1])
    ax3.set_title("Comparison to original: |error|")
    ax3.set_xlabel("x")
    ax3.set_ylabel("y")
    ax3.grid(alpha=0.1, color="white")
    cbar = plt.colorbar(im_err, ax=ax3, fraction=0.046, pad=0.04)
    cbar.set_label("error", fontsize=9)
    fig3.tight_layout()

    return fig1, fig2, fig3


@st.fragment
def render() -> None:
    """
    Main orchestration function.
    Flow: Setup → Stage 1 (forward) → Stage 2 (reconstruction) → Summary insights
    """
    st.subheader("Projection Slice Theorem")
    st.caption("From line integrals to reconstruction: each projection contributes one central Fourier slice.")
    st.latex(r"\mathcal{F}_t\{p_\theta(t)\}(\omega) = \mathcal{F}_{2D}\{f(x,y)\}(\omega\cos\theta,\, \omega\sin\theta)")
    data = _build_phantom()

    # ==================== STAGE 1: FORWARD PROBLEM ====================
    st.markdown("---")
    st.subheader("Stage 1: Single projection anatomy")
    st.write(
        "A single projection at angle θ is a line integral through the object. "
        "Its 1D Fourier transform gives frequency components along that direction."
    )
    theta_deg = st.slider("Angle for Stage 1 (deg)", 0.0, 179.0, 45.0, 1.0)
    
    fig_obj, fig_proj, fig_fft = _plot_forward_stage(data, theta_deg)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.pyplot(fig_obj, clear_figure=True)
    with col2:
        st.pyplot(fig_proj, clear_figure=True)
    with col3:
        st.pyplot(fig_fft, clear_figure=True)


    # ==================== STAGE 2: RECONSTRUCTION CHALLENGE ====================
    st.markdown("---")
    st.subheader("Stage 2: Reconstruction from multiple angles")
    num_angles = st.slider("Number of angles for Stage 2 reconstruction", 2, 64, 16, 2)
    st.write(
        f"Collect {num_angles} projections at different angles to sample many, but not all, "
        "central Fourier slices. From this incomplete frequency grid, inverse FFT reconstructs an image "
        "that we compare directly to the original."
    )

    with st.spinner(f"Reconstructing from {num_angles} angles..."):
        sparse_fft, hit_count = _build_sparse_fft_from_angles(data["image"], data["x"], data["freq"], num_angles)
        reconstructed = _reconstruct_from_sparse_slices(sparse_fft, hit_count)
        mse = float(np.mean((data["image"] - reconstructed) ** 2))
        psnr = 10 * np.log10(1.0 / (mse + 1e-12)) if mse > 0 else 100.0

    sampled_pixels = int(np.count_nonzero(hit_count > 0))
    total_pixels = int(hit_count.size)
    sampled_pct = 100.0 * sampled_pixels / max(total_pixels, 1)
    st.caption(
        f"Reconstruction uses {sampled_pixels} / {total_pixels} sampled frequency pixels ({sampled_pct:.1f}%)."
    )

    show_overlay = st.toggle("Show original as overlay on reconstruction")
    fig_sparse_fft, fig_recon, fig_err = _plot_reconstruction_stage(data, sparse_fft, reconstructed, show_overlay=show_overlay)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.pyplot(fig_sparse_fft, clear_figure=True)
    with c2:
        st.pyplot(fig_recon, clear_figure=True)
    with c3:
        st.pyplot(fig_err, clear_figure=True)

    # ==================== INTERPRETATION ====================
    st.markdown("---")
    if mse < 0.01:
        st.success(f"✓ Strong reconstruction: MSE = {mse:.5f}, PSNR = {psnr:.1f} dB")
        st.write("Error is concentrated in fine details. Low frequencies are well-captured by many angle overlaps.")
    elif mse < 0.05:
        st.info(f"△ Moderate reconstruction: MSE = {mse:.5f}, PSNR = {psnr:.1f} dB")
        st.write("Error shows structure. Higher angles needed for finer detail.")
    else:
        st.warning(f"⚠ Limited reconstruction: MSE = {mse:.5f}, PSNR = {psnr:.1f} dB")
        st.write("Error is significant. High-frequency information is sparse or missing.")

    _, angles_unique = _effective_unique_angles(num_angles, len(data["freq"]))
    st.caption(
        f"Using {len(angles_unique)} effective unique rays from {num_angles} requested angles. "
        f"Finite grid resolution causes angle overlap.")


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
