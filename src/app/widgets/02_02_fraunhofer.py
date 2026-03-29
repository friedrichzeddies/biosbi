import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io
from PIL import Image


DISPLAY_AMPLITUDE_SCALE = 0.65

WAVELENGTH = 0.25
SLIT_WIDTH = 2
X_MIN = -6.0
GRID_SIZE = 220
SLIT_SAMPLES = 101
FRAMES = 48
FPS = 24
FRAUNHOFER_REFERENCE_DISTANCE = (SLIT_WIDTH ** 2) / WAVELENGTH
OBSERVATION_DISTANCE_MAX = float(np.ceil(30.0 * FRAUNHOFER_REFERENCE_DISTANCE))
OBSERVATION_DISTANCE_MIN = 0.2
AMPLITUDE_AXIS_MAX = 1.2
THEORY_ZERO_COUNT = 4.0
MIN_Y_HALF_SPAN = 2.0


def _field_to_rgb(field: np.ndarray, cmap_name: str = "RdBu_r") -> np.ndarray:
	"""Convert normalized scalar field in [-1, 1] to RGB uint8."""
	norm = (field + 1.0) / 2.0
	norm = np.clip(norm, 0.0, 1.0)
	rgba = plt.get_cmap(cmap_name)(norm)
	rgb = (rgba[..., :3] * 255).astype(np.uint8)
	return rgb


def _dynamic_y_half_span(observation_distance: float) -> float:
	"""Set y span from sinc zero spacing: y1 = lambda * z / a."""
	first_zero = (WAVELENGTH * observation_distance) / SLIT_WIDTH
	half_span = THEORY_ZERO_COUNT * first_zero
	return max(MIN_Y_HALF_SPAN, float(half_span))


def _build_payload(observation_distance: float) -> dict:
	x_vals = np.linspace(-observation_distance/2, observation_distance, GRID_SIZE)
	y_half_span = _dynamic_y_half_span(observation_distance)
	y_vals = np.linspace(-y_half_span, y_half_span, GRID_SIZE)
	xx, yy = np.meshgrid(x_vals, y_vals, indexing="xy")

	k = 2 * np.pi / WAVELENGTH
	left_mask = xx < 0.0
	right_mask = xx > 0.0

	# Incoming planar wave from negative x toward positive x.
	amp_left = np.exp(1j * k * xx) * left_mask

	# Diffracted field on the right: Huygens sources sampled across the slit at x=0.
	slit_y = np.linspace(-SLIT_WIDTH / 2.0, SLIT_WIDTH / 2.0, SLIT_SAMPLES)
	x_right = xx[right_mask]
	y_right = yy[right_mask]

	dx = x_right[np.newaxis, :]
	dy = y_right[np.newaxis, :] - slit_y[:, np.newaxis]
	r = np.sqrt(dx * dx + dy * dy)
	r = np.maximum(r, 1e-6)

	weights = np.ones(SLIT_SAMPLES, dtype=float)
	weights[0] = 0.5
	weights[-1] = 0.5
	delta_y = SLIT_WIDTH / (SLIT_SAMPLES - 1)
	integral_weights = (weights * delta_y)[:, np.newaxis]

	diffracted_samples = np.exp(1j * k * r) / np.sqrt(r)
	right_values = np.sum(diffracted_samples * integral_weights, axis=0)

	amp_right = np.zeros_like(xx, dtype=np.complex128)
	amp_right[right_mask] = right_values

	# Aperture line x=0: only open inside slit.
	mid_mask = np.abs(xx) < ((x_vals[1] - x_vals[0]) * 0.7)
	aperture_mask = mid_mask & (np.abs(yy) <= (SLIT_WIDTH / 2.0))
	amp_mid = np.exp(1j * k * xx) * aperture_mask

	amp_total = amp_left + amp_right + amp_mid

	return {
		"x_vals": x_vals,
		"y_vals": y_vals,
		"amp_real": amp_total.real.astype(np.float32),
		"amp_imag": amp_total.imag.astype(np.float32),
		"observation_distance": float(observation_distance),
	}


def _render_diffraction_frames(payload: dict) -> list:
	"""Render one period of the wave field as RGB frames."""
	x_vals = np.array(payload["x_vals"], dtype=float)
	y_vals = np.array(payload["y_vals"], dtype=float)
	real_part = payload["amp_real"].astype(np.float64)
	imag_part = payload["amp_imag"].astype(np.float64)
	amp_complex = real_part + 1j * imag_part
	x0_idx = int(np.argmin(np.abs(x_vals)))
	slit_open_mask = np.abs(y_vals) <= (SLIT_WIDTH / 2.0)
	wall_mask = ~slit_open_mask

	rgb_frames = []
	times = np.linspace(0.0, 1.0, FRAMES, endpoint=False)

	for time_t in times:
		omega_t = 2 * np.pi * time_t
		field = np.real(amp_complex * np.exp(-1j * omega_t))
		field_abs_max = np.max(np.abs(field))
		if field_abs_max > 0:
			field = (field / field_abs_max) * DISPLAY_AMPLITUDE_SCALE
		rgb = _field_to_rgb(field)

		# Draw an opaque wall at x=0 and keep a bright slit opening visible.
		for x_idx in [x0_idx, min(x0_idx + 1, rgb.shape[1] - 1)]:
			rgb[wall_mask, x_idx, :] = np.array([25, 25, 25], dtype=np.uint8)
			rgb[slit_open_mask, x_idx, :] = np.array([245, 235, 60], dtype=np.uint8)

		rgb_frames.append(rgb)

	return rgb_frames


@st.cache_data(show_spinner=False)
def _generate_diffraction_gif_bytes(payload: dict) -> bytes:
	"""Generate GIF bytes from payload (cached)."""
	rgb_frames = _render_diffraction_frames(payload)
	
	pil_frames = [Image.fromarray(frame) for frame in rgb_frames]
	gif_buffer = io.BytesIO()
	frame_duration_ms = int(1000 / FPS)
	
	pil_frames[0].save(
		gif_buffer,
		format="GIF",
		save_all=True,
		append_images=pil_frames[1:],
		duration=frame_duration_ms,
		loop=0,
		optimize=False,
	)
	
	return gif_buffer.getvalue()


def _extract_measured_amplitude(payload: dict) -> tuple:
	x_vals = np.array(payload["x_vals"], dtype=float)
	y_vals = np.array(payload["y_vals"], dtype=float)
	real_part = np.array(payload["amp_real"], dtype=float)
	imag_part = np.array(payload["amp_imag"], dtype=float)

	amp_complex = real_part + 1j * imag_part
	x_idx = int(np.argmin(np.abs(x_vals - float(payload["observation_distance"]))))
	measured = np.abs(amp_complex[:, x_idx])

	return y_vals, measured


def _theoretical_sinc_amplitude(y_vals: np.ndarray, observation_distance: float) -> np.ndarray:
	arg = np.pi * SLIT_WIDTH * y_vals / (WAVELENGTH * observation_distance)
	# Keep distance scaling so the peak decreases with increasing z.
	theory = (1.0 / np.sqrt(observation_distance)) * np.abs(np.sinc(arg / np.pi))
	return theory



@st.fragment
def fraunhofer_diffraction_widget() -> None:
	st.header("Single-Slit Propagation: Near Field to Far Field")
	st.caption(
		"A planar wave enters from negative x and passes through one slit at x=0. "
		"Increase the observation distance to approach the Fraunhofer (Fourier/sinc) regime."
	)

	col1, col2, col3 = st.columns([1, 1, 1.5])

	with col1:
		with st.form("fraunhofer_form"):
			st.markdown("### Observation")
			observation_distance = st.slider(
				"Max $x$ (observation distance)",
				min_value=OBSERVATION_DISTANCE_MIN / 2,
				max_value=OBSERVATION_DISTANCE_MAX / 2,
				value=1.0,
				step=0.2,
				help=(
					"Upper limit is chosen from the Fraunhofer scale $x >> a^2/\lambda$. "
					f"Here $a^2/\lambda = {FRAUNHOFER_REFERENCE_DISTANCE:.2f}$, so max $x = {OBSERVATION_DISTANCE_MAX:.1f}$."
				),
			)
			st.caption("Choose parameters freely, then click 'Apply' once to run the simulation.")
			submitted = st.form_submit_button("Apply Parameters", type="primary")

			if submitted:
				st.session_state["fraunhofer_payload"] = _build_payload(float(observation_distance))

	if "fraunhofer_payload" not in st.session_state:
		st.session_state["fraunhofer_payload"] = _build_payload(1.0)

	if "fraunhofer_payload" in st.session_state:
		config = st.session_state["fraunhofer_payload"]

		with col2:
			st.markdown("#### 2D Wave Propagation")
			with st.spinner("Computing diffraction GIF..."):
				gif_bytes = _generate_diffraction_gif_bytes(config)
			st.image(gif_bytes, caption="Planar incident wave and slit diffraction", width="content")

		with col3:
			st.markdown("#### Amplitude at $x = \max x$")

			y_vals, measured = _extract_measured_amplitude(config)
			fig, ax = plt.subplots(figsize=(6.5, 4.0))
			ax.plot(y_vals, measured, color="#1f77b4", linewidth=2.2, label="Simulated amplitude")

			fresnel_num = (SLIT_WIDTH ** 2) / (WAVELENGTH * float(config["observation_distance"]))
			regime = "Far Field" if fresnel_num < 1.0 else "Near Field"
			
			show_theory = st.toggle("Show theoretical result", value=False)
			
			if show_theory:
				theory = _theoretical_sinc_amplitude(y_vals, float(config["observation_distance"]))
				theory_peak = float(np.max(theory))
				measured_peak = float(np.max(measured))
				if theory_peak > 0.0:
					theory = theory * (measured_peak / theory_peak)
				ax.plot(y_vals, theory, "--", color="#d62728", linewidth=2.0, label="Fraunhofer sinc (scaled)")

			ax.set_xlabel("y")
			ax.set_ylabel("Amplitude magnitude")
			#ax.set_ylim(0.0, AMPLITUDE_AXIS_MAX)
			#ax.grid(True, alpha=0.3)
			ax.legend()
			ax.set_title(f"Regime: {regime} ($x = {config['observation_distance']:.1f}$, Fresnel $N = {fresnel_num:.2f}$)")
			fig.tight_layout()
			st.pyplot(fig)
