# Lenses, PSF, and CTF: When Optics Becomes a Model

We now pick up directly from the previous section: if Fourier space is the practical language, we need a physical model that tells us what the microscope actually does in that language. This is where lenses, point-spread functions, and transfer functions stop being textbook vocabulary and start becoming the core of image interpretation.

In an ideal world, a single point in the object would appear as a single point on the detector, perfectly sharp and perfectly faithful. In the world we actually live in, that point is spread into a small pattern, and this pattern is what we call the point-spread function, or PSF. Once you accept that every object is made of many such points, the full image is naturally modeled as a convolution:

$$
\mathrm{Image} = \mathrm{Object} * \mathrm{PSF}
$$

This is already a complete statement, but in practice it is often easier to reason in Fourier space, where convolution becomes multiplication:

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathcal{F}(\mathrm{PSF})
$$

and with the standard definition

$$
\mathrm{CTF} := \mathcal{F}(\mathrm{PSF}),
$$

we get the compact expression

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF}.
$$

This one equation is incredibly useful, because it says in plain terms that the microscope does not preserve all spatial frequencies equally; instead, it modulates them, sometimes strongly, and those modulations are exactly what later shape what we can and cannot recover.

The lens perspective matters here because focal planes are not just geometric conveniences. In Fourier optics, they are where frequency content becomes physically organized, which is why the back focal plane is treated as a Fourier plane in both intuition and practice.

## Try it yourself

In the interaction below, use your previous frequency-masking intuition as a stand-in for transfer behavior and deliberately suppress or keep different frequency bands while watching the real-space consequences. The goal here is not to memorize formulas but to build the instinct that frequency-domain manipulation and image-domain appearance are two sides of the same operation.

TODO-widget (high priority): Lens Fourier-plane explorer. Expected outcome: understand how plane waves map to focal-plane points and why front and back focal planes are central to Fourier-optics reasoning.

TODO-widget (high priority): PSF convolution sandbox. Expected outcome: connect specific PSF shapes to blur behavior in real space and to modulation behavior in Fourier space.

## Before we move on

You now have a coherent imaging model that links optics and algebra without hand-waving. The next step is to extend this from 2D image intuition to 3D scattering geometry so we can explain why a single projection is only a slice of the full story.
