# ⚠️ Experimental Repository

**PLEASE NOTE:** This repository is currently in an experimental state. Most of the code and documentation here is **not our own work** and is based on existing repositories (primarily [flatironinstitute/cryoSBI](https://github.com/flatironinstitute/cryoSBI)). We are currently experimenting with this codebase for research and development purposes.

---

## 🚀 Streamlit Application Structure

The interactive portion of this repository (the Cat Projector) is built using Streamlit. Here is how it is structured:

- **`app/main.py`**: The main entry point. Run the app using:
  ```bash
  streamlit run app/main.py
  ```
- **`app/content/`**: Contains Markdown files (e.g., `intro.md`) that provide the textual descriptions and documentation displayed in the app.
- **`app/widgets/`**: Contains Python scripts (e.g., `cat_projector.py`) that define the interactive components, sliders, and visualization logic.

### 🛠 Debugging and Development

- **Writing/Debugging Text**: You can individually edit and debug the text by modifying the `.md` files in `app/content/`. Streamlit's hot-reloading will update the app in real-time.
- **Writing/Debugging Widgets**: The logic for widgets is encapsulated in standalone functions within `app/widgets/`. You can import these functions into a standard Python script or Jupyter Notebook to debug logic, data processing, or visualization independently of the Streamlit UI.

---

# cryoSBI - Simulation-based Inference for Cryo-EM

![Testing Status](https://github.com/DSilva27/cryo_em_SBI/actions/workflows/python-package.yml/badge.svg?branch=main)

## Summary
cryoSBI is a Python module for simulation-based inference in cryo-electron microscopy. The module provides tools for simulating cryo-EM particles, training an amortized posterior model, and sampling from the posterior distribution.
The code is based on the SBI library [Lampe](https://lampe.readthedocs.io/en/stable/), which uses PyTorch.

## Installing
To install the module, you will have to download the repository and create a virtual environment with the required dependencies.
You can create an environment, for example, with conda:
```bash
conda create -n cryoSBI python=3.10
```
After creating the virtual environment, install the required dependencies and the module.

## Dependencies
1. [Lampe](https://lampe.readthedocs.io/en/stable/)
2. [SciPy](https://scipy.org/)
3. [NumPy](https://numpy.org/)
4. [PyTorch](https://pytorch.org/get-started/locally/)
5. `json`
6. [mrcfile](https://pypi.org/project/mrcfile/)

## Download this repository
```bash
git clone https://github.com/flatironinstitute/cryoSBI.git
```

## Navigate to the cloned repository and install the module
```bash
cd cryoSBI
pip install .
```

## Tutorial
An introduction tutorial can be found at `tutorials/tutorial.ipynb`. In this tutorial, we go through the whole process of making models for cryoSBI, training an amortized posterior, and analyzing the results.
The following sections highlight cryoSBI's key features.

## Generate model file to simulate cryo-EM particles
To generate a model file for simulating cryo-EM particles with the simulator provided in this module, you can use the command line tool `models_to_tensor`.
You will need either a set of pdbs which are indexed or a trr trajectory file which contains all models. The tool will generate a model file that can be used to simulate cryo-EM particles.

```bash
models_to_tensor \
    --model_file path_to_models/pdb_{}.pdb \
    --output_file path_to_output_file/output.pt \
    --n_pdbs 100
```
The output file will be a PyTorch tensor with the shape `(number of models, 3, number of pseudo atoms)`.

## Simulating cryo-EM particles
To simulate cryo-EM particles, use the `CryoEmSimulator` class. It takes a simulation config file and simulates cryo-EM particles based on specifying parameters.

```python
from cryo_sbi import CryoEmSimulator
simulator = CryoEmSimulator("path_to_simulation_config_file.json")
images, parameters = simulator.simulate(num_sim=10, return_parameters=True)
```

The simulation config file should be a JSON file with the following structure:
```json
{   
    "N_PIXELS": 128,
    "PIXEL_SIZE": 1.5,
    "SIGMA": [0.5, 5.0],
    "MODEL_FILE": "path_to_models/models.pt",
    "SHIFT": 25.0,
    "DEFOCUS": [0.5, 2.0],
    "SNR": [0.001, 0.5],
    "AMP": 0.1,
    "B_FACTOR": [1.0, 100.0] 
}
```
- **Pixel size**: Defined in Angström (Å).
- **Atom sigma**: Defines the size of the Gaussians used to approximate the protein's electron density.
- **Shift**: Offset of the protein from the image centre in Angström (Å).
- **Defocus**: Units of micrometres (μm).
- **SNR**: Signal-to-noise ratio (unitless).
- **Amplitude**: Unitless parameter (0 to 1).
- **B-factor**: Units of Angström squared (Å^2).

## Training an amortized posterior model
Training can be done using the `train_npe_model` command line utility.

```bash
train_npe_model \
    --image_config_file path_to_simulation_config_file.json \
    --train_config_file path_to_train_config_file.json \
    --epochs 150 \
    --estimator_file posterior.estimator \
    --loss_file posterior.loss \
    --n_workers 4 \
    --simulation_batch_size 5120 \
    --train_device cuda
```

The training config file structure:
```json
{
    "EMBEDDING": "RESNET18",
    "OUT_DIM": 256,
    "NUM_TRANSFORM": 5,
    "NUM_HIDDEN_FLOW": 10,
    "HIDDEN_DIM_FLOW": 256,
    "MODEL": "NSF",
    "LEARNING_RATE": 0.0003,
    "CLIP_GRADIENT": 5.0,
    "THETA_SHIFT": 25,
    "THETA_SCALE": 25,
    "BATCH_SIZE": 256
}
```

## Loading the posterior after training
```python
import cryo_sbi.utils.estimator_utils as est_utils
posterior = est_utils.load_estimator(
    config_file_path="path_to_config_file",
    estimator_path="path_to_estimator_file", 
    device="cuda"
)
```

## Inference
```python
import cryo_sbi.utils.estimator_utils as est_utils
samples = est_utils.sample_posterior(
    estimator=posterior,
    images=images,
    num_samples=20000,
    batch_size=100,
    device="cuda",
)
```

## Latent space
```python
import cryo_sbi.utils.estimator_utils as est_utils
latent_vecs = est_utils.compute_latent_repr(
    estimator=posterior,
    images=images,
    batch_size=100,
    device="cuda",
)
```

Visualize with UMAP:
```python
import umap
reducer = umap.UMAP(metric="euclidian", n_components=2, n_neighbors=50)
embedding = reducer.fit_transform(latent_vecs.numpy())
```
