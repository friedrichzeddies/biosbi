# Fourier Intuition Part II: The Same Story in 2D

What you just did in 1D was already the real idea, and now we only change the stage. Instead of decomposing a line signal into 1D components, we decompose an image into 2D plane-wave components with orientation and spatial frequency.

This is the moment where Fourier language starts to feel directly relevant for Cryo-EM, because our data are images and because many imaging effects are easier to understand in frequency space than in pixel space.

## Try it yourself

In the next interaction, tune individual 2D components and watch the reconstruction update. Try to identify which components mainly shape global geometry and which ones sharpen finer, more local structure.

Once this feels natural, we move one step further and start masking parts of Fourier space on purpose, which is exactly the kind of operation that prepares us for understanding transfer functions.
