### Ewald Sphere and Projection-Slice: Why One Image Is Never the Whole Truth

Up to now, we have stayed in a mostly 2D mindset because it builds intuition quickly. Real biological specimens, however, are 3D, and the measurement geometry is inherently 3D as well.

Instead of a thin mask, we model the specimen as a 3D scattering potential $V(x,y,z)$. In the far field, the scattered signal is directly linked to the 3D Fourier transform of that object, but there is a hard geometric constraint: one single image cannot sample all of reciprocal space.

In mathematical language, we describe the incident beam by the wave with vector $\mathbf{k}_0$, the scattered beam as $\mathbf{k}$, and define the scattering vector

$$
\mathbf{q} = \mathbf{k} - \mathbf{k}_0.
$$

For elastic scattering, magnitudes are conserved,

$$
|\mathbf{k}| = |\mathbf{k}_0|,
$$

which means the allowed scattering geometry lies on the so called Ewald sphere of radius $|\mathbf{k}|$.

This concept is rooted in diffraction physics. When describing how a crystal scatters waves, one can prove that reciprocal lattice points (i.e., the Fourier transform of the lattice) must intersect with this sphere for diffraction to occur. Wherever this intersection happens, we observe a diffraction spot.

In cryo-EM, the typical accelerating voltages make electron wavelengths exceptionally small. For example, at around 200 keV, $\lambda$ is roughly $0.025$ Ångströms, meaning the sphere radius in *reciprocal* space ($1/\lambda$) is immensely large. Over the relatively tiny frequency range we care about in a single-particle image, that sphere looks almost completely flat. This is exactly why one micrograph is often treated mathematically as an approximate 2D Fourier slice.

In the widget right after this paragraph, three quick checks make the idea stick very fast:

1. Increase voltage from low to high values and watch how the effective electron wavelength changes.
2. Compare electron and X-ray curvature in reciprocal-space geometry.
3. Tilt the lattice and track which spots satisfy the Ewald condition.
