# Ewald Sphere and Projection-Slice: Why One Image Is Never the Whole Truth

Up to now we stayed in a mostly 2D mindset because it builds intuition quickly. Real specimens, however, are 3D, and the measurement geometry is 3D as well. This is exactly the point where explanations often become hand-wavy, so we keep the logic explicit.

Instead of a thin mask, we model the specimen as a 3D scattering potential $V(x,y,z)$. In the far field, the scattered signal is linked to the 3D Fourier transform of that object, but there is a hard geometric constraint: one image does not sample all of reciprocal space.

Write the incident beam as $\mathbf{k}_0$, the scattered beam as $\mathbf{k}$, and define the scattering vector

$$
\mathbf{q} = \mathbf{k} - \mathbf{k}_0.
$$

For elastic scattering, magnitudes are conserved,

$$
|\mathbf{k}| = |\mathbf{k}_0|,
$$

which means the allowed scattering geometry lies on an Ewald sphere.

Now comes the cryo-EM-specific punchline. At typical accelerating voltages, electron wavelengths are very small. For example, at around 200 keV, $\lambda$ is roughly $0.025$ Angstrom, so the sphere radius $1/\lambda$ is large. Over the frequency range we care about in a single particle image, that sphere looks almost flat. This is why one micrograph is often treated as an approximate 2D Fourier slice.

This directly gives the projection-slice statement in plain language: a 2D projection image corresponds to a 2D slice through the 3D Fourier transform of the object. Rotate the particle, rotate the slice. Collect many orientations, and those slices can be assembled into a 3D description. That is not just a lecture slogan, it is the geometric backbone of SPA.

If you open the widget right after this paragraph, three quick checks make the idea stick very fast:

1. Increase voltage from low to high values and watch how the effective electron wavelength changes.
2. Compare electron and X-ray curvature in reciprocal-space geometry.
3. Tilt the lattice and track which spots satisfy the Ewald condition.

If you can explain why the electron Ewald curve is close to flat in this regime, you already understand why projection-slice reasoning works so well in cryo-EM.

At this point, one thing should feel concrete: one beautiful projection is still incomplete information. Next we quantify how many differently oriented slices we need before a reconstruction becomes reliable.
