import numpy as np
import matplotlib.pyplot as plt
import streamlit as st


@st.cache_resource
def _physical_constants() -> dict:
    return {
        "h": 6.62607015e-34,
        "m_e": 9.1093837015e-31,
        "e": 1.602176634e-19,
        "c": 299792458.0,
    }


def _electron_wavelength_angstrom(acc_voltage_keV: float) -> float:
    const = _physical_constants()
    voltage_v = float(acc_voltage_keV) * 1e3
    numerator = const["h"]
    denominator = np.sqrt(
        2.0
        * const["m_e"]
        * const["e"]
        * voltage_v
        * (1.0 + (const["e"] * voltage_v) / (2.0 * const["m_e"] * const["c"] ** 2))
    )
    wavelength_m = numerator / denominator
    return wavelength_m * 1e10


def _make_reciprocal_spots(d_spacing_angstrom: float, max_index: int, tilt_deg: float) -> np.ndarray:
    g0 = 1.0 / float(d_spacing_angstrom)
    idx = np.arange(-max_index, max_index + 1)
    hh, kk = np.meshgrid(idx, idx, indexing="xy")
    points = np.stack([hh.ravel() * g0, kk.ravel() * g0], axis=1)
    points = points[(points[:, 0] != 0.0) | (points[:, 1] != 0.0)]

    rot = np.deg2rad(float(tilt_deg))
    rot_matrix = np.array([[np.cos(rot), -np.sin(rot)], [np.sin(rot), np.cos(rot)]])
    return points @ rot_matrix.T


def _ewald_match_mask(spots: np.ndarray, k: float, tolerance: float) -> np.ndarray:
    center = np.array([0.0, k])
    dist = np.linalg.norm(spots - center, axis=1)
    return np.abs(dist - k) <= tolerance


def _ewald_branches(k: float, x_vals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    inside = np.abs(x_vals) <= k
    y_lower = np.full_like(x_vals, np.nan, dtype=float)
    y_upper = np.full_like(x_vals, np.nan, dtype=float)
    radial = np.sqrt(np.maximum(k**2 - x_vals[inside] ** 2, 0.0))
    y_lower[inside] = k - radial
    y_upper[inside] = k + radial
    return y_lower, y_upper


def _plot_spot_interaction(spots: np.ndarray, k_electron: float, k_xray: float, tolerance: float, xlim: float) -> tuple:
    x_vals = np.linspace(-xlim, xlim, 500)

    y_e, _ = _ewald_branches(k_electron, x_vals)
    y_x_lower, y_x_upper = _ewald_branches(k_xray, x_vals)

    mask_e = _ewald_match_mask(spots, k_electron, tolerance)
    mask_x = _ewald_match_mask(spots, k_xray, tolerance)

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.5), sharex=True, sharey=True)

    for ax, title, curve, mask, upper_curve in zip(
        axes,
        [f"Electron (k={k_electron:.2f} Å⁻¹)", f"X-ray λ=1.0 Å (k={k_xray:.2f} Å⁻¹)"],
        [y_e, y_x_lower],
        [mask_e, mask_x],
        [None, y_x_upper],
    ):
        ax.scatter(spots[:, 0], spots[:, 1], s=12, color="#b0b0b0", alpha=0.6)
        if np.any(mask):
            ax.scatter(
                spots[mask, 0],
                spots[mask, 1],
                s=45,
                color="#d62728",
                edgecolors="black",
                linewidths=0.3,
                zorder=5,
            )
        ax.plot(x_vals, curve, color="#1f77b4", linewidth=2.4, alpha=0.6, label="Ewald curve")
        if upper_curve is not None:
            ax.plot(x_vals, upper_curve, color="#1f77b4", linewidth=1.8, alpha=0.45, linestyle="--")
        ax.axhline(0.0, color="#2ca02c", linestyle=":", linewidth=1.5, alpha=0.6)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("kx (Å⁻¹)", fontsize=10)
        ax.grid(alpha=0.2)

    axes[0].set_ylabel("ky (Å⁻¹)", fontsize=10)
    axes[0].legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    return fig, int(np.sum(mask_e)), int(np.sum(mask_x))


@st.fragment
def render() -> None:
    st.write("#### Ewald Sphere: Reciprocal Lattice Interaction")
    st.caption("Compare how electrons (flat Ewald) vs X-rays (curved Ewald) interact with the crystal lattice.")

    c1, c2, c3 = st.columns(3)
    with c1:
        acc_voltage_keV = st.slider("Voltage (keV)", 40.0, 400.0, 200.0, 5.0)
    with c2:
        d_spacing = st.slider("Lattice d (Å)", 0.8, 5.0, 2.0, 0.2)
    with c3:
        tilt_deg = st.slider("Lattice tilt (°)", -85.0, 85.0, 25.0, 5.0)

    config = {
        "voltage": float(acc_voltage_keV),
        "d": float(d_spacing),
        "tilt": float(tilt_deg),
    }

    lam_e = _electron_wavelength_angstrom(config["voltage"])
    k_e = 1.0 / lam_e
    k_x = 1.0 / 1.0

    spots = _make_reciprocal_spots(d_spacing_angstrom=config["d"], max_index=5, tilt_deg=config["tilt"])
    g0 = 1.0 / config["d"]
    tol = 0.10 * g0
    xlim = max(1.5 * np.max(np.abs(spots[:, 0])), 2.5 * g0)

    fig, hits_e, hits_x = _plot_spot_interaction(
        spots=spots, k_electron=k_e, k_xray=k_x, tolerance=tol, xlim=xlim
    )

    col_plot, col_info = st.columns([1.4, 0.6])
    with col_plot:
        st.pyplot(fig, clear_figure=True)

    with col_info:
        st.metric("Electron λ", f"{lam_e:.4f} Å")
        st.metric("Diffracting spots (e⁻)", hits_e)
        st.metric("Diffracting spots (X-ray)", hits_x)
        st.markdown("---")
        st.caption(
            f"**Red dots** = spots on Ewald condition (diffracting). **Electrons** at {config['voltage']:.0f} keV produce "
            "nearly flat curvature → local lattice plane projection. **X-rays** show strong curvature."
        )


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render()
