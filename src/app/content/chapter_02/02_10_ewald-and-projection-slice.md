# Ewald Sphere and Projection-Slice: Why One Image Is Never the Whole Truth

Up to now we deliberately stayed in a 2D mindset because it builds intuition quickly, but real specimens are three-dimensional objects, and the geometry of what can be measured is therefore three-dimensional too. This is exactly where many explanations suddenly become vague, so let us keep the chain of logic explicit.

Instead of a thin mask, we now model the specimen as a 3D scattering potential $V(x,y,z)$. In the far field, the scattered signal is connected to the 3D Fourier transform of that object, but there is a strict geometric constraint that prevents us from sampling all of reciprocal space in one shot.

Write the incident beam as $\mathbf{k}_0$, the scattered beam as $\mathbf{k}$, and define the scattering vector

$$
\mathbf{q} = \mathbf{k} - \mathbf{k}_0.
$$

For elastic scattering, magnitudes are conserved,

$$
|\mathbf{k}| = |\mathbf{k}_0|,
$$

which means the allowed scattering geometry lies on an Ewald sphere. Because electron wavelengths are tiny, the sphere radius $1/\lambda$ is huge, so near the origin the sampled region appears almost flat, and this is why a micrograph is often interpreted as an approximate Fourier slice.

This gives us the projection-slice theorem in plain language: a 2D projection image corresponds to a 2D slice through the 3D Fourier transform of the object. Rotate the particle, rotate the slice; collect many orientations, and you can assemble a 3D description. That is not just a nice sentence for lectures, it is the geometric backbone of SPA.

## Try it yourself

TODO-widget (critical): Ewald and projection-slice 3D explorer. Expected outcome: manipulate illumination direction and collection angle, inspect the sampled spherical cap, and map detector coordinates to reciprocal-space slices.

Until that dedicated interaction exists, use the Fourier interaction below as an intuition bridge and imagine each manipulated spectrum as one orientation-dependent slice rather than a complete 3D object signature.

## Before we move on

You should now have a clear reason why one beautiful projection is still incomplete information. In the next part, we return to the transfer side and look at what the CTF and low-dose noise do to the slices we actually observe.
