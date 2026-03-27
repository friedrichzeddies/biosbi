# CTF in Real Cryo-EM Images: Why Raw Data Looks So Unforgiving

From the previous section we carry one crucial relation forward,

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF},
$$

and this is exactly where many first encounters with real micrographs become emotionally rough, because once you internalize this equation you realize that the microscope does not simply record structure; it reshapes frequency content in a highly selective way before you ever see the image.

That is why raw Cryo-EM images can look strangely low-contrast, inverted in places, or generally hard to parse at first glance. CTF zero crossings remove information at specific frequencies, oscillations can flip contrast, and envelope terms damp high-frequency detail, so two images of the same underlying object can look surprisingly different under different imaging settings.

Now add dose limits. We cannot blast fragile biological samples with unlimited electrons, so we operate in low-dose regimes where single-image signal-to-noise ratio is poor. The difficult combination is that frequencies can be weakened by CTF behavior before noise is even considered, and then noise further obscures what remains. This is not a failure of interpretation skill; it is the native operating condition of the experiment.

## Try it yourself

In the interaction below, treat frequency masking as a first proxy for transfer effects and deliberately suppress different bands while comparing the real-space outcome. The important habit is to connect every Fourier-side change with an expected visual consequence, because that reflex will later make CTF discussions feel practical instead of ceremonial.

TODO-widget (critical): physics-parameterized CTF explorer. Controls should include defocus, spherical aberration, envelope or B-like damping, and optional amplitude contrast. Expected outcome: map parameter changes to zero-crossing positions and corresponding image artifacts.

## Before we move on

You now have the right expectation: a single cryo image is noisy and transfer-modulated by design, not by accident. The next step is to show how many such imperfect views can still be combined into reliable 3D structure through SPA.
