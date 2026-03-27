# Projection-Slice and Orientation Coverage: Why One View Is Never Enough

Once Ewald geometry is in place, the next statement becomes easier to trust: one projection gives one orientation-dependent Fourier slice, not the whole 3D information of the object.

So even a very clean single image is still fundamentally incomplete. The way out is to image many particles in many orientations, so different slices accumulate and cover enough of 3D Fourier space for reconstruction.

There is one useful pattern to remember. Low spatial frequencies are sampled redundantly because almost every slice passes through the center of reciprocal space. High spatial frequencies are harder: they are direction-specific and need many well-distributed orientations. This is exactly why reconstructions often recover broad shape first and fine detail later.

Another practical point: more views help, but gains are not linear forever. At finite pixel size, some additional angles become partially redundant. In other words, there is a point where you still improve, but with diminishing returns.

When you explore the widget, it helps to go in this order:

1. Start with a very small number of angles and inspect the reconstruction error.
2. Increase angle count step by step and watch how MSE and PSNR change.
3. Pay attention to which features appear early (global shape) and which appear late (fine structure).

Quick self-check: if quality still improves at 32 angles but only a little compared with 16, can you explain that using finite sampling and slice overlap?

If this feels like the conceptual bridge to SPA, that is exactly right. Next we return to optics and transfer effects, because orientation coverage is only one part of the real imaging bottleneck.
