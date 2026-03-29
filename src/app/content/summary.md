_Have you read both pages? If so, you can now continue to the summary. Else, go up and see the next chapter._

## Summary

That was a lot of content, no question. But if you zoom out, it all follows one clean thread from beginning to end.

### One-Line Thread

We came from understanding how cryo-EM images are physically generated, identify what information is distorted or lost, and then try to infer what remains learnable with uncertainty-aware Bayesian methods.

### The Story As One Pipeline

1. Waves interfere.
   Image contrast starts from interference, not from arbitrary visual patterns.

2. Interference leads to diffraction, and diffraction leads to Fourier space.
   Under Fraunhofer conditions, diffraction is the Fourier transform of the object or aperture.

3. The microscope applies a transfer function.
   With PSF in real space and CTF in Fourier space, image formation follows

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF}.
$$

So the microscope behaves like a frequency-dependent filter: some frequencies pass, some are attenuated, some are lost, and some can even flip contrast.

4. A single projection is physically valid but informationally incomplete.
   Projection-slice and Ewald-sphere geometry explain why one 2D view is only one slice of 3D information.

5. Real cryo-EM data is noisy by design.
   Low-dose imaging protects molecules but lowers SNR; together with CTF effects, raw data is low-contrast and hard to interpret directly.

6. SPA counters this with many views.
   Alignment and averaging improve SNR, but structural heterogeneity means orientation and conformation still have to be disentangled.

7. This naturally motivates SBI.
   Forward simulation is feasible, exact likelihoods are often not, so we learn posteriors from simulated data.

8. We learn a Neural Posterior Estimate to infer a plausible conformation given a new image based on what we have seen in training.

9. We need to assess whether we can trust what comes out based on what we fixed in our setup.

### Chapter 2 in Compact Form: Imaging Physics

The key takeaway from Chapter 2 is simple: cryo-EM is fundamentally a Fourier-domain imaging problem.

Real space and Fourier space are two views of the same object. Low spatial frequencies carry global structure, while high spatial frequencies carry fine detail but are much harder to recover reliably. Better orientation coverage improves reconstruction quality, especially at low frequencies. So if something feels "missing" in the data, that is usually not a mistake - it is a direct consequence of the acquisition regime.

### Chapter 3 in Compact Form: Inference

Once physics defines the forward process, Chapter 3 turns to the inverse problem. In compact notation:

- Observation: $x$ (image)
- Target parameters: $\theta$ (e.g., conformation)
- Nuisance parameters: $\eta$ (orientation, noise, imaging settings)

Neural posterior estimation aims to learn

$$
q(\theta\mid x) \approx p(\theta\mid x),
$$

which gives calibrated uncertainty rather than only point predictions. That matters whenever different parameter settings can generate very similar images.

### Why The Workflow Makes Sense

SBI is particularly useful here because it is amortized:

1. Spend computation upfront on simulation and training.
2. Perform fast posterior inference at test time.

For high-dimensional images, representation learning (for example ResNet summaries) first compresses observations. A flexible density estimator (for example normalizing flows) then models the resulting complex posteriors.

### Validation Is a Crucial Part of the Method

Robust evaluation needs three checks, and each one answers a different question:

1. Internal validation: does the model match the simulated training distribution?
2. External validation: does simulation transfer to real data sufficiently well?
3. Calibration (SBC): over many simulated trials, ranks of true parameters should be approximately uniform.

Passing only internal checks is not enough if simulator assumptions miss important real-world effects.

### Final Takeaway

The whole project forms one continuous bridge:
wave physics -> image formation limits -> uncertainty-aware Bayesian inversion.

Our assessment throughout this project was designed to stay as intuitive as possible, so ideas become usable, not just memorized. We hope you now see both cryo-EM physics and SBI from a more intuitive perspective and feel confident transferring these concepts to other domains. And if you are curious to go further, we would be very happy if you try the original source code with actual proteins and explore where your own questions lead.

Thank you for participating, and until we meet again.

Sebi and Friedel
