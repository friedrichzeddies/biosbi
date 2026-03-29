## _Have you read both pages? If so, you can now continue to the summary. Else, go up and see the next chapter._

## Summary

This chapter sequence is dense, but it follows one clean logic from beginning to end.

### One-Line Thread

Understand how cryo-EM images are physically generated, identify what information is distorted or lost, then infer what remains learnable with uncertainty-aware Bayesian methods.

### The Story As One Pipeline

1. Waves interfere.
   Image contrast starts from interference, not from arbitrary visual patterns.

2. Interference leads to diffraction, and diffraction leads to Fourier space.
   Under Fraunhofer conditions, diffraction is the Fourier transform of the object/aperture.

3. The microscope applies a transfer function.
   With PSF in real space and CTF in Fourier space, image formation follows

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF}.
$$

So the microscope behaves like a frequency-dependent filter: some frequencies pass, some are attenuated, some are lost, some may flip contrast.

4. A single projection is physically valid but informationally incomplete.
   Projection-slice and Ewald-sphere geometry explain why one 2D view is just one slice of 3D information.

5. Real cryo-EM data is noisy by design.
   Low-dose imaging protects molecules but lowers SNR; combined with CTF effects, raw data is low-contrast and hard to interpret directly.

6. SPA counters this with many views.
   Alignment and averaging improve SNR, but structural heterogeneity means orientation and conformation must be disentangled.

7. This naturally motivates SBI.
   Forward simulation is feasible, exact likelihoods are often not, so we learn posteriors from simulated data.

### Chapter 2 in Compact Form: Imaging Physics

The key outcome of Chapter 2 is that cryo-EM is fundamentally a Fourier-domain imaging problem.

- Real space and Fourier space are complementary views of the same object.
- Low spatial frequencies carry global structure.
- High spatial frequencies carry fine detail but are harder to recover reliably.
- Better orientation coverage improves reconstruction, especially at low frequencies.
- Data limitations are not mistakes; they are a consequence of the acquisition regime.

### Chapter 3 in Compact Form: Inference

Once physics defines the forward process, Chapter 3 addresses the inverse problem:

- Observation: $x$ (image)
- Target parameters: $\theta$ (e.g., conformation)
- Nuisance parameters: $\eta$ (orientation, noise, imaging settings)

Neural posterior estimation aims to learn

$$
q(\theta\mid x) \approx p(\theta\mid x),
$$

which provides calibrated uncertainty instead of only point predictions. This is essential when different parameter settings can produce similar images.

### Why The Workflow Makes Sense

SBI is useful here because it is amortized:

1. Spend computation upfront on simulation and training.
2. Perform fast posterior inference at test time.

For high-dimensional images, representation learning (e.g., ResNet summaries) compresses observations before a flexible density estimator (e.g., normalizing flows) models complex posteriors.

### Validation Is Part of the Method, Not an Extra

Robust evaluation needs three checks:

1. Internal validation: does the model match the simulated training distribution?
2. External validation: does simulation transfer to real data sufficiently well?
3. Calibration (SBC): over many simulated trials, ranks of true parameters should be approximately uniform.

Passing only internal checks is not enough if simulator assumptions miss important real-world effects.

### Final Takeaway

The project forms a continuous bridge:
wave physics -> image formation limits -> uncertainty-aware Bayesian inversion.

Short version: simulate forward, infer backward, and validate calibration rigorously.
