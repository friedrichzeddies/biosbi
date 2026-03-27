# Lenses, PSF, and CTF: When Optics Becomes a Model

If Fourier space is our practical language, we now need a physical model that tells us what the microscope actually does in that language. This is where lenses, PSF, and CTF stop being textbook vocabulary and become daily working tools.

In an ideal world, one point in the object would map to one point on the detector. In reality, that point is spread into a small pattern. That pattern is the point-spread function (PSF). If every object is a sum of many points, image formation naturally becomes convolution:

$$
\mathrm{Image} = \mathrm{Object} * \mathrm{PSF}
$$

This is already a complete model, but in practice it is often easier in Fourier space, where convolution becomes multiplication:

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

This equation is useful because it says, very directly, that the microscope does not preserve all frequencies equally. Some frequencies are passed well, some are attenuated, and some can even change sign in contrast.

Defocus is one of the key reasons this gets interesting. Defocus introduces phase shifts that depend on spatial frequency. Those shifts create the oscillatory CTF behavior, including zero crossings where specific frequencies are effectively lost in that image.

The lens perspective matters because focal planes are not just geometric convenience. In Fourier optics, the back focal plane physically organizes frequencies. So this is a real optical effect, not just math notation.

If you jump into the widget here, this mini checklist usually makes the behavior click quickly:

1. Increase defocus and watch where CTF oscillations and zero crossings move.
2. Increase B-factor and inspect how high frequencies get damped.
3. Change amplitude contrast and observe how the transfer curve shape changes.

The goal is not memorizing formulas. The goal is building the reflex that parameter changes in Fourier space have predictable visual consequences in image space.

You now have a coherent image-formation model linking optics and algebra without hand-waving. Next we apply this directly to real cryo-EM images and explain why raw micrographs often look much harder than expected.
