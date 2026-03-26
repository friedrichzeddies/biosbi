# Lenses, PSF, and CTF: The Physics Version of What You Just Did by Hand

In the previous interaction you masked frequencies manually and watched the image change. A microscope does something similar physically, except it does it through optics rather than sliders.

If one point in the object were imaged perfectly, we would get one point on the detector. Real systems blur that point into a small pattern, called the PSF. Once every object is treated as many points, image formation becomes convolution,

$$
\mathrm{Image} = \mathrm{Object} * \mathrm{PSF},
$$

and in Fourier space this turns into multiplication,

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathcal{F}(\mathrm{PSF}).
$$

We call $\mathcal{F}(\mathrm{PSF})$ the CTF, so the microscope acts as a frequency-dependent modulator. That is the formal version of the intuition you already built with masks.

## Try it yourself

TODO-widget (high priority): Lens Fourier-plane explorer. Expected outcome: understand why focal planes are Fourier-organized spaces and how plane-wave content maps there.

TODO-widget (high priority): PSF convolution sandbox. Expected outcome: connect blur behavior in real space to modulation behavior in Fourier space.

From here we move into 3D scattering geometry, because even with a perfect CTF model, one projection still does not give the full 3D structure.
