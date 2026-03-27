# SPA, Sample Prep, and Heterogeneity: Turning Messy 2D Data into 3D Structure

We now connect everything we built so far. We have noisy projections, transfer-function distortions, and only slice-wise access to a 3D object in reciprocal space, so the natural question is how this can ever lead to a trustworthy 3D reconstruction. SPA is the practical answer, and it works precisely because we do not rely on one perfect image but on many imperfect ones.

The core idea is simple and elegant: image many copies of the same particle, each frozen in some random orientation, estimate how those orientations relate, and then combine the information so that reciprocal-space coverage accumulates. One projection contributes one slice-like view; many orientations give many views; enough views give reconstructable 3D information.

Averaging is central because single-particle images are noisy by design. If you align particles that truly correspond to the same orientation and state, signal adds coherently while random noise tends to cancel, and that is why class averages can look dramatically cleaner than any one raw particle image.

This is also why sample preparation is not a side chapter for biochemists only. Biological structure depends on aqueous context, electron microscopy needs vacuum, and vitrification is the compromise that lets us preserve near-native states while making imaging physically possible. Reconstruction quality is therefore downstream of physics, computation, and preparation all at once.

Then comes the twist that makes biology interesting and analysis difficult: molecules are not rigid statues. They occupy multiple conformations, and if those states are mixed during averaging, important structural differences get blurred away. In practice, this means sorting by orientation is often not enough; we also need to account for conformational heterogeneity.

## Try it yourself

TODO-widget (high priority): SPA orientation and averaging explorer. Expected outcome: observe how alignment quality and particle count influence signal-to-noise gains in class averages.

TODO-widget (high priority): conformation-mixing explorer. Expected outcome: compare averaging within a single state versus averaging across mixed states and inspect the resulting structural blur.

Optional bridge interaction from the next chapter can be used here to build intuition for why inverse decisions remain ambiguous unless uncertainty is modeled explicitly.

## Before we move on

You now have a complete physical and computational motivation for why Cryo-EM naturally leads into probabilistic inference. The next chapter picks up exactly there and frames the reconstruction challenge in the language of simulation-based inference.
