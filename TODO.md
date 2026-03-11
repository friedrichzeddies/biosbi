# Cryo-EM + SBI Project TODO

Goal: build an intuitive yet realistic pipeline for cryo-EM forward simulation and
parameter inference using Simulation-Based Inference (SBI), inspired by
Dingeldein et al. (2024).

Approach:
Start with very simple models (toy densities, no noise) and gradually increase
complexity toward realistic cryo-EM imaging conditions.

Core pipeline:

θ (parameters) → forward simulator → image x → SBI inference → posterior p(θ | x)



--------------------------------------------------
WORK PACKAGE 1 — Define Parameterization
--------------------------------------------------

[ ] Decide parameter vector θ

Possible parameters:
- rotation / orientation
- translation (x,y)
- particle scale
- defocus
- noise level
- CTF parameters

Minimal start:

θ = (rotation, translation_x, translation_y)

Later extensions:

θ = (rotation, translation_x, translation_y, defocus, noise)

Questions / Notes:
- Which parameters are identifiable?
- Which parameters affect image most strongly?



--------------------------------------------------
WORK PACKAGE 2 — Toy Density Generator
--------------------------------------------------

Goal: create simple synthetic 2D/3D objects to build intuition.

[ ] Implement density generators

Possible objects:
- Gaussian blob
- circle
- rectangle
- multiple blobs
- "cow-shaped" mask

Tasks:

[ ] Implement function

    generate_density(params)

[ ] Visualization tools
    plot density

Challenges / Notes:
- resolution / grid size
- continuous vs discrete density



--------------------------------------------------
WORK PACKAGE 3 — Projection Operator
--------------------------------------------------

Goal: simulate cryo-EM projection.

Model:

3D density → projection along beam axis → 2D image

Tasks:

[ ] implement projection

    image(x,y) = ∫ density(x,y,z) dz

[ ] rotation of volume before projection

[ ] test with simple shapes

Validation:

[ ] verify rotation behaves correctly
[ ] visualize projection results

Challenges:
- interpolation artifacts
- discretization



--------------------------------------------------
WORK PACKAGE 4 — Imaging Physics
--------------------------------------------------

Goal: approximate TEM image formation.

Forward pipeline:

density
  → projection
  → Fourier transform
  → CTF filtering
  → detector noise

Tasks:

[ ] implement FFT-based pipeline

[ ] implement simplified CTF model

Possible parameters:
- defocus
- frequency cutoff

[ ] add noise model

Start simple:

Gaussian noise

Later:

Poisson / shot noise

Questions:
- how realistic does the model need to be?
- what level of complexity still allows inference?



--------------------------------------------------
WORK PACKAGE 5 — Forward Simulator Interface
--------------------------------------------------

Goal: produce a simulator compatible with SBI.

Required function:

simulator(θ) → image

Tasks:

[ ] implement wrapper

    def simulator(theta):
        return image

[ ] sampling from prior distribution

    θ ~ p(θ)

[ ] dataset generation

    {θ_i , x_i}

Validation:

[ ] visualize parameter → image mapping



--------------------------------------------------
WORK PACKAGE 6 — Progressive Difficulty Ladder
--------------------------------------------------

Goal: gradually increase complexity.

Define simulation regimes:

LEVEL 1
[ ] simple blob
[ ] no noise

LEVEL 2
[ ] blob
[ ] Gaussian noise

LEVEL 3
[ ] complex shapes
[ ] CTF filtering

LEVEL 4
[ ] protein-like density
[ ] low SNR

Questions:

- where does inference break down?
- which parameters become ambiguous?



--------------------------------------------------
WORK PACKAGE 7 — SBI Inference
--------------------------------------------------

Use SBI framework.

Tasks:

[ ] connect simulator to SBI

[ ] define prior distributions

example:

rotation ~ Uniform(0, 2π)
translation ~ Uniform(-5, 5)

[ ] train neural posterior estimator

[ ] run inference on simulated images

Outputs:

posterior p(θ | x)

Validation:

[ ] compare inferred parameters to true θ



--------------------------------------------------
WORK PACKAGE 8 — Parameter Recovery Experiments
--------------------------------------------------

Goal: test inference quality.

Experiments:

[ ] parameter recovery plots

true θ vs inferred θ

[ ] posterior visualization

[ ] uncertainty vs noise level

Metrics:

- mean error
- posterior variance



--------------------------------------------------
WORK PACKAGE 9 — Robustness Experiments
--------------------------------------------------

Goal: explore limitations of the method.

Experiment ideas:

NOISE SWEEP

[ ] vary SNR
[ ] measure inference accuracy


MODEL MISMATCH

Train simulator with:

Gaussian noise

Test with:

Poisson noise


CTF MISMATCH

Train with simplified CTF
Test with modified CTF

Questions:

- how robust is SBI to simulator mismatch?



--------------------------------------------------
WORK PACKAGE 10 — Connection to Dingeldein et al.
--------------------------------------------------

Goal: anchor project to the paper but extend it.

Possible tasks:

[ ] reproduce one key experiment or figure

[ ] compare results using own simulator

Extensions:

[ ] use own generated data
[ ] change inference parameters
[ ] test additional noise models



--------------------------------------------------
OPTIONAL EXTENSIONS
--------------------------------------------------

If time permits:

[ ] load real protein density
[ ] generate projections from PDB structure
[ ] test inference on real-like structures

Possible pipeline:

PDB → voxel density → projection → cryo-EM image



--------------------------------------------------
OPEN QUESTIONS / IDEAS
--------------------------------------------------

- Which parameters are easiest to infer?
- Which imaging effects destroy information?
- Does inference degrade smoothly with noise?
- Can SBI detect model mismatch?

