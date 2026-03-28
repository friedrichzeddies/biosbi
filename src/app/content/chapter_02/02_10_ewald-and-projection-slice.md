### Ewald Sphere and Projection-Slice: Why One Image Is Never the Whole Truth

Up to now we stayed in a mostly 2D mindset because it builds intuition quickly. Real specimens, however, are 3D, and the measurement geometry is 3D as well.

Instead of a thin mask, we model the specimen as a 3D scattering potential $V(x,y,z)$. In the far field, the scattered signal is linked to the 3D Fourier transform of that object, but there is a hard geometric constraint: one image does not sample all of reciprocal space.

In mathematical language, we describe the incident beam by the wave with vector $\mathbf{k}_0$, the scattered beam as $\mathbf{k}$, and define the scattering vector

$$
\mathbf{q} = \mathbf{k} - \mathbf{k}_0.
$$

For elastic scattering, magnitudes are conserved,

$$
|\mathbf{k}| = |\mathbf{k}_0|,
$$

which means the allowed scattering geometry lies on the so called Ewald sphere of radius $|\mathbf{k}|$.

This roots in diffraction physics. When describing how a crystal behaves upon scattering, one can proof that reciprocal lattice points (i.e. the Fourier transform of the lattice) can intersect with this sphere. And whereever this happens, we observe a diffraction spot after the interaction.

In Cryo-EM, the typical accelerating voltages make electron wavelengths very small. For example, at around 200 keV, $\lambda$ is roughly $0.025$ Angstrom, so the sphere radius in _reciprocal_ space $1/\lambda$ is large. Over the frequency range we care about in a single particle image, that sphere looks almost flat. This is why one micrograph is often treated as an approximate 2D Fourier slice.

In the widget right after this paragraph, three quick checks make the idea stick very fast:

1. Increase voltage from low to high values and watch how the effective electron wavelength changes.
2. Compare electron and X-ray curvature in reciprocal-space geometry.
3. Tilt the lattice and track which spots satisfy the Ewald condition.
