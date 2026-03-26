# CTF in Real Cryo-EM Images: Why Raw Data Feels Harsh at First

Even if geometry gives us the right slices, what we record is still filtered by microscope transfer behavior, and that is why raw images often look much harder to read than newcomers expect.

The key relation remains

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF},
$$

which means some spatial frequencies are damped, some are phase-inverted, and some can disappear near zero crossings. So yes, two images of the same structure can look surprisingly different if acquisition conditions differ.

Now combine this with low-dose constraints. We keep dose low to avoid damaging biological samples, so single images are noisy from the start. In practice, this means we are not trying to recover a pristine signal; we are trying to recover structure from noisy, transfer-modulated observations.

## Try it yourself

Use the frequency-masking interaction as a proxy for transfer effects and deliberately remove different frequency bands while tracking how the real-space image changes. This is still the fastest way to make CTF consequences feel tangible.

TODO-widget (critical): physics-parameterized CTF explorer. Expected outcome: link defocus and envelope-like parameters to zero locations and visible image artifacts.

The natural consequence of this section is SPA: if one image is noisy and filtered, we need many views and careful averaging to recover robust structure.
