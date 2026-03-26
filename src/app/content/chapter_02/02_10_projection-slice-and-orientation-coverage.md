# Projection-Slice and Orientation Coverage: Why One View Is Never Enough

Once Ewald geometry is in place, the next statement becomes much easier to trust: one projection image corresponds to one orientation-dependent slice in reciprocal space, not the full 3D information of the object.

That means a single clean image can still be fundamentally incomplete. The way out is to image many particles in many orientations, so different slices accumulate and eventually cover enough of 3D Fourier space to support reconstruction.

## Try it yourself

TODO-widget (critical): projection-slice and orientation-coverage explorer. Expected outcome: rotate a particle, watch the reciprocal-space slice rotate with it, and track how multi-view coverage fills 3D space.

If this feels like the conceptual bridge to SPA, that is exactly right. The next sections bring back transfer effects and noise, then connect everything to practical averaging workflows.
