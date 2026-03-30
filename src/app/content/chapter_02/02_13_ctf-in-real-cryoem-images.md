### CTF in Real Cryo-EM Images: Why Raw Data Looks So Unforgiving

From the previous section we carry one crucial relation forward,

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF}.
$$

A microscope does not simply record structure. It reshapes frequency content before you ever see the image.

That is why raw cryo-EM images can look low-contrast, partly inverted, or just confusing at first glance. CTF zero crossings remove information at specific frequencies. Oscillations can flip contrast. Envelope terms damp high-frequency detail. So two images of the same object can look surprisingly different under different settings.

Now add dose limits. We cannot blast fragile biological samples with unlimited electrons, so we operate in a low-dose regime where the single-image *signal-to-noise ratio* (SNR) is extremely poor. The hard combination is this: the CTF weakens part of the frequency content first, then noise further obscures what remains. This is not a failure of interpretation skill. It is the native, unfiltered operating condition of the experiment.

This is exactly why averaging, and inference later on, are so critical. You do not recover structure by finding one magical image; you recover it by combining many transfer-modulated, extremely noisy views in a physically consistent way.

This full picture brings us back to our introductory quiz. Below, you can play around with the full simulation pipeline of the cat. Check if all these physical concepts are intuitively clear to you by now.
