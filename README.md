# biosbi

Interactive teaching and experimentation app for cryo-EM and simulation-based inference. A GNN final project.

## Motivation

This project combines interactive visual explanations with runnable simulations so ideas from diffraction, Fourier space, and SBI become easier to explore. The goal is to move from static notes to a hands-on learning workflow where you can tweak parameters and immediately see what changes.

## Requirements

- Python 3.12 or newer
- uv (brew install)

## Setup

Clone the repository:

```
git clone git@github.com:friedrichzeddies/biosbi.git
```

Locally install the required packages.

```bash
uv sync
```

## Run The Server

```bash
uv run streamlit run src/app/main.py
```

The app will open in your browser after Streamlit starts.

## Workflow

1. Start the app with Streamlit.
2. Edit lesson text in `src/app/content/` (Markdown files).
3. Edit interactive logic in `src/app/widgets/`.
4. Reload the browser to see updates (or let Streamlit auto-refresh).

For focused widget debugging, you can also run a single widget file directly, for example:

```bash
uv run streamlit run src/app/widgets/02_09_full-simulation-pass.py
```
