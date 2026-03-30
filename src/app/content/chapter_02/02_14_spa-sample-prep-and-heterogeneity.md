At this stage, it is worth sanity-checking your intuition: why can a sharper-looking image still miss crucial frequencies? Why does changing the defocus move information loss across frequency bands? And why is low-dose imaging not optional in cryo-EM? If those three questions feel answerable in your own words, you are in an excellent place for this final section.

You now have the right expectation: a single cryo image is noisy and transfer-modulated by design, not by accident. Next, we close Chapter 2 by connecting all these physical phenomena to the SPA workflow, sample preparation, and conformational heterogeneity.

### SPA, Sample Prep, and Heterogeneity: Turning Messy 2D Data into 3D Structure

We have noisy projections, transfer-function distortions, and only slice-wise access to a 3D object in reciprocal space. The natural question is: how can this ever become a trustworthy 3D reconstruction? Single Particle Analysis (*SPA*) is the practical answer, and it works exactly because we do not rely on one perfect image.

The core idea is simple and elegant: image many instances of the same object (e.g. a protein), each frozen in a random orientation, estimate how those orientations relate, and combine the information so reciprocal-space coverage accumulates. One projection contributes one slice-like view. Many orientations give many views. Enough views give reconstructable 3D information.

Averaging is central because single-particle images are noisy by design. If you align particles that truly correspond to the same orientation and state, signal adds coherently while random noise tends to cancel. That is why class averages can look dramatically cleaner than any single raw particle image.

### Sample Preparation

This is also why sample preparation is not a side topic for biochemists only. Biological structure depends on aqueous context, while electron microscopy needs vacuum. Vitrification (*very* fast freezing) is the compromise that preserves near-native states while keeping imaging physically possible. Reconstruction quality is therefore downstream of physics, computation, and preparation at the same time.

Then comes the twist that makes biology interesting and analysis difficult: molecules are not rigid statues. They occupy multiple *conformations*. That means that the proteins can have multiple different shapes based on their environment or internal chemistry. Those are often linked to the functions they perform. Almost like our cat; it needs to lie down when it eats but for walking around it typically stands up.

If those states (conformations) are mixed during averaging, important structural differences get blurred away because they underlying spatial structure is different (although it is still the same protein/cat). In practice, sorting by orientation is often not enough; we also need to account for conformational heterogeneity before building class averages. 

You have already had a glimpse at some realistically simulated EM images. You can image that infering whether the cat is lying down or standing up from this noisy mess is rather difficult. And you are correct.

### Motivation for Part 2

We will transition to the SBI part of the module with one simple question: Can we make this incredibly difficult, but physically well-understood process easier? Can we learn to infer the conformation from a newly gathered image by relying on ones we've already seen computationally?
