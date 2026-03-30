Next we return to optics and transfer effects, because orientation coverage is only one part of the real imaging bottleneck.

### Lenses, PSF, and CTF: When Optics Becomes a Model

If Fourier space is our practical language, we now need a physical model that tells us what the microscope actually does in that language. This is where we introduce lenses[^1] and transfer functions.

[^1]: Lenses were initially the main limiting component in EM, as we require *electromagnetic* lenses to manipulate the beam. It took significant R&D to alter these short-wavelength beams precisely.

One way to think about lenses is to accept that they act as physical fourier transforms. A helpful model of an imaging system is called a 4f system:

A 4f system consists of two lenses separated by the sum of their focal lengths, with the object placed in the front focal plane of the first lens. The first lens performs a Fourier transform, mapping the spatial structure of the object onto its back focal plane — effectively placing the object’s frequencies on a physical plane. The second lens then takes that plane and performs an inverse Fourier transform, reconstructing the image in its back focal plane. In this way, the 4f setup translates between real space and Fourier space. Keep this duality between spaces in mind for the following excursion.

In an ideal world, one point in the object would map to one point on the detector. In reality, that point is spread into a small pattern. That pattern is the _point-spread function_ (PSF). If every object is a "sum" of many points, image formation naturally becomes convolution:

$$
\mathrm{Image} = \mathrm{Object} * \mathrm{PSF}
$$

The PSF serves as a great diagnostic tool to see how far away the microscope if from "reality". It characterises micropscope performance and lets characterise imaging defects. This is already a complete model, but in practice it is often easier in Fourier space, where convolution becomes multiplication:

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathcal{F}(\mathrm{PSF})
$$

and with the standard definition[^2]

[^2]: This is true under the so-called weak-phase approximation, which generally holds for our specific case.

$$
\mathrm{CTF} := \mathcal{F}(\mathrm{PSF}),
$$

where we defined the *Contrast Transfer Function* (CTF), giving us the compact expression:

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF}.
$$

This equation is useful because it says, very directly, that the microscope does not preserve all frequencies equally. Some frequencies are passed well, some are attenuated, and some can even change sign in contrast.

Defocus is one of the key parameters. It introduces phase shifts that depend on spatial frequency. These shifts create the oscillatory CTF behavior, including zero crossings where specific frequencies are effectively lost in the resulting image. Another parameter is the envelope strength, described by the $B$-factor, alongside the amplitude contrast.

In the interactive widget below, play around with the defocus (introducing oscillations), manipulate the B-factor (damping), and change the amplitude contrast to observe how the transfer curve's shape responds.
