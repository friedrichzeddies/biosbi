### CTF in Real Cryo-EM Images: Why Raw Data Looks So _Difficult_

From the previous section we carry one crucial relation forward,

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF}.
$$

A microscope does not simply record structure. It reshapes frequency content before you ever see the image.

That is why raw cryo-EM images can look low-contrast, partly inverted, or just confusing at first glance. CTF zero crossings remove information at specific frequencies. Oscillations can flip contrast. Envelope terms damp high-frequency detail. So two images of the same object can look surprisingly different under different settings.

Now add dose limits. We cannot blast fragile biological samples (or poor little kitty cats) with unlimited electrons, so we operate in a low-dose regime where single-image _signal-to-noise ratio_ (SNR) is poor. The hard combination is this: CTF weakens part of the frequency content first, then noise further obscures what remains. This is not really a lack of skill, but rather it is the native operating condition of the experiment.

This is also why averaging and inference are so important later. You do not recover structure by finding one ✨magical✨ image. You recover it by combining many transfer-modulated, noisy views in a physically consistent way.

The full picture is now close to our quiz in the beginning and the final stage of our data generation process, relevant for inference. Below, you should play around with the simulation of the cat and check if all concepts are clear by now.
