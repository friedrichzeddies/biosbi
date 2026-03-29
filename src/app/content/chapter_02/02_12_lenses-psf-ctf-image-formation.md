Next we return to optics and transfer effects, because orientation coverage is only one part of the real imaging bottleneck.

### Lenses, PSF, and CTF: When Optics Becomes a Model

If Fourier space is our practical language, we now need a physical model that tells us what the microscope actually does in that language. This is where we introduce lenses[^1], and transfer functions.

The lens perspective matters because focal planes are not just geometric convenience. In Fourier optics, the back focal plane physically organizes frequencies.

[^1]: Lenses were the main component first limiting EM, as we need _electromagnetic_ lenses to manipulate the beam. It took some time of R&D to alter these small wavelength beams precisely.

In an ideal world, one point in the object would map to one point on the detector. In reality, that point is spread into a small pattern. That pattern is the _point-spread function_ (PSF). If every object is a "sum" of many points, image formation naturally becomes convolution:

$$
\mathrm{Image} = \mathrm{Object} * \mathrm{PSF}
$$

This is already a complete model, but in practice it is often easier in Fourier space, where convolution becomes multiplication:

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathcal{F}(\mathrm{PSF})
$$

and with the standard definition[^2]

[^2]: This is true for the so called weak phase and amplitude approximation, which generally holds for our case.

$$
\mathrm{CTF} := \mathcal{F}(\mathrm{PSF}),
$$

where we defined the _contrast transfer function_ (CTF), we get the compact expression

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF}.
$$

This equation is useful because it says, very directly, that the microscope does not preserve all frequencies equally. Some frequencies are passed well, some are attenuated, and some can even change sign in contrast.

Defocus is one of the key parameters. Defocus introduces phase shifts that depend on spatial frequency. Those shifts create the oscillatory CTF behavior, including zero crossings where specific frequencies are effectively lost in that image. Another one is the envelope strength, ddescibed by the $B$-Factor, and we also can define the amplitude behavior.

If you jump into the widget here, play around with the defocus (introduce oscillations), manipulate the B-factor (damping) and change amplitude contrast and observe how the transfer curve shape changes.
