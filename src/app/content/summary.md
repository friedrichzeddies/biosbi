## Summary

If this felt like a lot: yes, absolutely. But the good news is that there is a surprisingly clean thread running through the whole project.

We started with waves and ended with Bayesian posteriors over cat conformations, and somehow this did not fall apart. In fact, the pieces lock together pretty well.

### The Big Story in One Line

Understand how images are physically formed, understand what information gets lost on the way, and then use simulation-based inference to recover what is still learnable, with uncertainty attached.

### Chapter 2: What Cryo-EM Images Really Are

### 1) Waves and interference are the foundation

The first core idea is simple and non-negotiable: image contrast begins with wave interference. Minima and maxima are not visual quirks; they are the physical signal.

Huygens helps build intuition here: wavefronts can be thought of as many tiny secondary sources, and from there diffraction behavior becomes less mysterious.

### 2) Diffraction naturally leads to Fourier space

Near field can look complicated and local, while far field reveals clean structure. Under the Fraunhofer approximation, diffraction at an aperture becomes a Fourier transform of the aperture/object.

That is one of the main conceptual pivots of the chapter: Fourier space is not math decoration. It is the practical language of imaging.

### 3) Fourier intuition matters more than formulas

The jump from 1D to 2D Fourier thinking is mostly a jump in intuition:

- Real space and frequency space are two coordinate views of the same object.
- Low spatial frequencies encode global shape.
- High spatial frequencies encode fine details and edges.
- Filtering in Fourier space creates predictable changes in real-space appearance.

This is exactly why frequency-space manipulations are so useful in cryo-EM.

### 4) Image formation is a transfer process

In real systems, points do not stay points. A point spreads by the PSF, so image formation is convolution in real space and multiplication in Fourier space.

With CTF defined as the Fourier transform of the PSF, we get the key model:

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF}.
$$

Practical consequence: the microscope is a frequency-dependent filter. Some frequencies are preserved, some damped, some lost (CTF zero crossings), and some can flip contrast.

### 5) One clean image is still incomplete information

Ewald sphere geometry and projection-slice logic explain why a single 2D projection is justified, but never enough to capture captures full 3D structure.

Even with high quality data, one view gives one orientation-dependent slice. Reconstructing 3D requires many orientations and good coverage.

Important pattern:

- Low frequencies are easier to cover (many slices pass the center).
- High frequencies are harder and orientation-sensitive.
- More views help, but gains eventually show diminishing returns.

### 6) Raw cryo-EM data is hard by design

Low-dose imaging is necessary to protect fragile samples, so single images have low SNR. Combine that with CTF modulation and you get exactly what we observe: noisy, low-contrast, often counterintuitive raw images.

This is not a user error. It is the operating regime.

### 7) SPA and sample prep connect physics to biology

Single-particle analysis works by combining many noisy, transfer-modulated projections of nominally the same object in many orientations.

Alignment and averaging improve SNR because signal adds coherently while noise partly cancels.

But biology adds the twist: conformational heterogeneity. Molecules are not rigid statues, so separating orientation and structural state becomes central.

### Chapter 3: Why SBI Is a Natural Next Step

### 1) Forward is easy, inverse is hard

In many scientific settings we can simulate observations from parameters, but cannot evaluate a tractable likelihood. That is the SBI regime.

We know how to go from parameters to image. We care about the reverse: given image, which parameters are plausible?

### 2) Bayesian framing clarifies the variables

- Observable variable: $x$ (the image).
- Explanatory variables: $\theta$ (what we actually care about, e.g. conformation).
- Nuisance variables: $\eta$ (orientation, noise, imaging conditions, etc.).

Priors matter because they define what is plausible before seeing data, and nuisance variability in simulation is essential for robust posteriors.

### 3) Learn posteriors, not just point guesses

Neural posterior estimation aims for

$$
q(\theta\mid x) \approx p(\theta\mid x).
$$

This gives uncertainty-aware answers, not only single labels. That is critical for ill-posed inverse problems where different parameter settings can explain similar images.

Cat intuition transfers cleanly: top-down views can make different poses look deceptively similar; a posterior can represent that ambiguity.

### 4) Amortized inference is the workflow advantage

SBI shifts effort to a heavy simulation/training phase, then performs fast inference on new observations. This is attractive when real experiments are expensive but simulation is comparatively cheap and scalable.

### 5) High-dimensional images need summaries

Images are large and not every pixel is equally informative. Summary networks (e.g. ResNets) compress observations into feature representations optimized for posterior inference.

Then a conditional density estimator, here based on normalizing flows, models complex posteriors (multi-modal, skewed, correlated) in a flexible and tractable way.

### 6) Validation is not optional

Good-looking outputs are not enough. We need to check:

- Internal validation: did we learn the simulated distribution well?
- External validation: is simulation close enough to reality?

A model can pass internal checks and still fail on real data if simulator assumptions miss important physics.

### 7) SBC gives a calibration sanity check

Simulation-based calibration uses a compact mantra:

The true parameter $\theta^*$ for a simulated trial should look like a typical draw from the inferred posterior.

Operationally:

1. Sample true parameters and nuisance settings from training priors.
2. Simulate an observation.
3. Draw posterior samples from the trained estimator.
4. Compute the rank of $\theta^*$ among those samples.

Over many trials, rank histograms should be approximately uniform if calibration is good.

For our cat setup, this becomes a direct and practical test of whether conformation uncertainty estimates are honest.

### Key Learnings to Keep

If you remember only a handful of things, keep these:

1. Cryo-EM image formation is fundamentally a Fourier-space story.
2. The microscope acts as a transfer function, not a perfect camera.
3. One projection is never the whole truth of a 3D object.
4. Noise and information loss are inherent constraints, not exceptions.
5. Inverse problems in this regime demand uncertainty-aware methods.
6. SBI lets us learn inverse mappings from simulations when likelihoods are intractable.
7. Calibration and misspecification checks are as important as raw predictive performance.

### Final Takeaway

This project is basically a carefully staged bridge:

from wave physics and imaging theory,
to realistic expectations about what data can and cannot tell us,
to modern Bayesian machine learning tools that turn those limits into actionable inference.

Or in short: simulate forward, infer backward, validate brutally, and keep your uncertainty estimates honest.
