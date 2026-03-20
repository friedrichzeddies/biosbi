import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io
import json
from PIL import Image

DISPLAY_AMPLITUDE_SCALE = 0.65

def _make_grid(extent: float, grid_size: int):
	"""Return 2D Cartesian grid in arbitrary length units."""
	x = np.linspace(-extent, extent, grid_size)
	xx, yy = np.meshgrid(x, x, indexing="xy")
	return xx, yy


def _wave_from_source(
	xx: np.ndarray,
	yy: np.ndarray,
	source_x: float,
	source_y: float,
	wavelength: float,
	phase: float,
	time_t: float,
	amplitude: float = 1.0
):
	"""Circular scalar wave from one source at a given time."""
	distance = np.sqrt((xx - source_x) ** 2 + (yy - source_y) ** 2)

	# Keep values finite at the source location.
	distance = np.maximum(distance, 1e-6)

	k = 2 * np.pi / wavelength
	omega = 2 * np.pi
	field = amplitude * np.cos(k * distance - omega * time_t + phase)
	return field


def _compose_field(
	xx: np.ndarray,
	yy: np.ndarray,
	sources: list,
	wavelength: float,
	time_t: float
):
	"""Sum field contributions from multiple wave origins."""
	total = np.zeros_like(xx, dtype=float)
	for src in sources:
		total += _wave_from_source(
			xx=xx,
			yy=yy,
			source_x=src["x"],
			source_y=src["y"],
			wavelength=wavelength,
			phase=src["phase"],
			time_t=time_t,
			amplitude=src.get("amplitude", 1.0)
		)
	return total


def _field_to_rgb(field: np.ndarray, cmap_name: str = "RdBu_r") -> np.ndarray:
	"""Convert normalized scalar field in [-1, 1] to RGB uint8."""
	norm = (field + 1.0) / 2.0
	norm = np.clip(norm, 0.0, 1.0)
	rgba = plt.get_cmap(cmap_name)(norm)
	rgb = (rgba[..., :3] * 255).astype(np.uint8)
	return rgb


def _render_wave_frames(payload: dict) -> list:
	"""Render one temporal period of wave fields as RGB frames."""
	grid_size = int(payload["grid_size"])
	extent = float(payload["extent"])
	wavelength = float(payload["wavelength"])
	frames = int(payload["frames"])

	sources = payload["sources"]
	xx, yy = _make_grid(extent=extent, grid_size=grid_size)

	rgb_frames = []
	times = np.linspace(0.0, 1.0, frames, endpoint=False)

	for time_t in times:
		field = _compose_field(
			xx=xx,
			yy=yy,
			sources=sources,
			wavelength=wavelength,
			time_t=time_t,
		)
		field_abs_max = np.max(np.abs(field))
		if field_abs_max > 0:
			# Keep colormap range fixed at [-1, 1] but reduce visual saturation.
			field = (field / field_abs_max) * DISPLAY_AMPLITUDE_SCALE
		rgb_frames.append(_field_to_rgb(field))

	return rgb_frames


@st.cache_data(show_spinner=False)
def _generate_gif_bytes(payload_json: str) -> bytes:
	"""Generate GIF bytes from a JSON payload (cached by payload)."""
	payload = json.loads(payload_json)
	rgb_frames = _render_wave_frames(payload)

	pil_frames = [Image.fromarray(frame) for frame in rgb_frames]
	gif_buffer = io.BytesIO()
	frame_duration_ms = int(1000 / max(1, int(payload["fps"])))

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


def _show_payload_and_gif(payload: dict, section_title: str) -> None:
	payload_json = json.dumps(payload, sort_keys=True)
	st.markdown(f"### {section_title}")
	with st.spinner("Computing one-period GIF..."):
		gif_bytes = _generate_gif_bytes(payload_json)
	st.image(gif_bytes, caption="One period (looping GIF)", width="content")


@st.fragment
def single_wave() -> None:
	st.header("2D Circular Wave Simulator")
	st.caption("Adjust sliders, then apply once to compute one period and play a smooth looping GIF.")
	col1, col2 = st.columns(2)

	with col1:
		with st.form("single_wave_form"):
			wavelength = st.slider("Wavelength", min_value=0.5, max_value=8.0, value=2.0, step=0.1)
			phase_1 = st.slider("Source phase (rad)", min_value=-float(np.pi), max_value=float(np.pi), value=0.0, step=0.05)
			source_x = st.slider("Source x", min_value=-8.0, max_value=8.0, value=0.0, step=0.1)
			source_y = st.slider("Source y", min_value=-8.0, max_value=8.0, value=0.0, step=0.1)
			frames = 48
			fps = 24
			st.caption("Choose parameters freely, then click 'Apply' once to run the simulation.")
			submitted = st.form_submit_button("Apply Parameters", type="primary")

			if submitted:
				st.session_state["single_wave_payload"] = {
					"grid_size": 320,
					"extent": 10.0,
					"wavelength": float(wavelength),
					"frames": int(frames),
					"fps": int(fps),
					"sources": [
						{"x": float(source_x), "y": float(source_y), "phase": float(phase_1), "amplitude": 1.0}
					],
				}

	if "single_wave_payload" in st.session_state:
		with col2:
			_show_payload_and_gif(st.session_state["single_wave_payload"], "Using your configuration.")


@st.fragment
def huygens_fresnel_widget() -> None:
	st.header("Two-Source Interference Simulator")
	st.caption(
		"Work on interference: source 1 is fixed; source 2 phase and position are adjustable."
	)
	col1, col2 = st.columns(2)

	with col1:
		with st.form("interference_wave_form"):
			wavelength = st.slider("Wavelength", min_value=0.5, max_value=8.0, value=2.0, step=0.1)
			phase_2 = st.slider("Variable source phase (rad)", min_value=-float(np.pi), max_value=float(np.pi), value=0.0, step=0.05)
			source2_x = st.slider("Variable source x", min_value=-8.0, max_value=8.0, value=3.0, step=0.1)
			source2_y = st.slider("Variable source y", min_value=-8.0, max_value=8.0, value=0.0, step=0.1)
			frames = 48
			fps = 24
			st.caption("Choose parameters freely, then click 'Apply' once to run the simulation.")
			submitted = st.form_submit_button("Apply Parameters", type="primary")

			if submitted:
				st.session_state["interference_wave_payload"] = {
					"grid_size": 320,
					"extent": 10.0,
					"wavelength": float(wavelength),
					"frames": int(frames),
					"fps": int(fps),
					"sources": [
						{"x": -3.0, "y": 0.0, "phase": 0.0, "amplitude": 1.0},
						{"x": float(source2_x), "y": float(source2_y), "phase": float(phase_2), "amplitude": 1.0},
					],
				}

	if "interference_wave_payload" in st.session_state:
		with col2:
			_show_payload_and_gif(st.session_state["interference_wave_payload"], "2 sources adjusted for phase")


@st.fragment
def multiple_sources_wave() -> None:
	st.header("Multiple Sources: Huygens' Principle")
	st.caption(
		"Explore planar wave formation with 2-50 closely-spaced sources all in phase. "
		"As you increase the number of sources, observe the emergence of a planar wavefront." \
        "How does the spacing and wavelength influences the wavefront?"
	)
	col1, col2 = st.columns(2)

	with col1:
		with st.form("multiple_sources_form"):
			num_sources = st.slider("Number of sources", min_value=2, max_value=50, value=5, step=1)
			wavelength = st.slider("Wavelength", min_value=0.5, max_value=8.0, value=2.0, step=0.1)
			source_spacing = st.slider("Source spacing (units)", min_value=0.05, max_value=1.0, value=0.3, step=0.05)
			frames = 48
			fps = 24
			st.caption("Choose parameters freely, then click 'Apply' once to run the simulation.")
			submitted = st.form_submit_button("Apply Parameters", type="primary")

			if submitted:
				# Create sources arranged in a vertical line, centered at y=0
				half_count = num_sources / 2.0
				sources = []
				for i in range(num_sources):
					y_pos = (i - half_count + 0.5) * float(source_spacing)
					sources.append({
						"x": -8.0,
						"y": y_pos,
						"phase": 0.0,
						"amplitude": 1.0
					})

				st.session_state["multiple_sources_payload"] = {
					"grid_size": 320,
					"extent": 10.0,
					"wavelength": float(wavelength),
					"frames": int(frames),
					"fps": int(fps),
					"sources": sources,
				}

	if "multiple_sources_payload" in st.session_state:
		with col2:
			payload = st.session_state["multiple_sources_payload"]
			num_src = len(payload["sources"])
			_show_payload_and_gif(payload, f"Planar wave from {num_src} sources")