# SPA, Sample Prep, and Heterogeneity: Making Reconstruction Work in Real Life

After Ewald geometry and CTF reality, SPA is no longer a buzzword but a necessity. One image is too incomplete and too noisy, so we combine many particle views and let information accumulate across orientations.

The idea is elegant but unforgiving in detail: align comparable particle views, average where appropriate, and use the resulting coverage in reciprocal space to reconstruct 3D structure. Signal reinforces across consistent views, while random noise tends to cancel.

This workflow only works if sample preparation preserves biologically meaningful structure in the first place, which is why vitrification and preparation quality are not side logistics but core scientific variables.

And then comes heterogeneity. Real molecules occupy multiple conformations, and if those states are mixed during averaging, important structural differences smear out. So practical pipelines often need to separate both orientation and conformation.

## Try it yourself

TODO-widget (high priority): SPA orientation and averaging explorer. Expected outcome: inspect how alignment quality and particle count affect class-average quality.

TODO-widget (high priority): conformation-mixing explorer. Expected outcome: compare within-state averaging versus mixed-state averaging and observe loss of structural specificity.

At this point the bridge to the next chapter is natural: once ambiguity and heterogeneity are explicit, probabilistic inference is not optional theory but a practical tool.
