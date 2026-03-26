# Ewald Sphere: The Geometric Constraint Behind What You Can Measure

Until now we mostly reasoned in 2D. For real specimens, that is not enough, because scattering lives in 3D reciprocal space and geometry decides which parts are accessible in one exposure.

If the incoming beam has wavevector $\mathbf{k}_0$ and scattered waves have $\mathbf{k}$, then elastic scattering requires

$$
|\mathbf{k}| = |\mathbf{k}_0|,
$$

so allowed scattering lies on a sphere. That is the Ewald sphere.

For electrons, $\lambda$ is small and the radius $1/\lambda$ is large, so near the origin the sampled region looks almost flat. This local flatness is one reason why projection data are often treated like slices.

## Try it yourself

TODO-widget (critical): Ewald geometry explorer. Expected outcome: vary beam and collection geometry and see which reciprocal-space region becomes accessible.

Next we make the slice statement explicit and connect Ewald geometry to why many orientations are required for 3D reconstruction.
