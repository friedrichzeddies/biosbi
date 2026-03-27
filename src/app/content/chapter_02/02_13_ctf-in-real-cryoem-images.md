# CTF in Real Cryo-EM Images: Why Raw Data Looks So Unforgiving

From the previous section we carry one crucial relation forward,

$$
\mathcal{F}(\mathrm{Image}) = \mathcal{F}(\mathrm{Object})\,\mathrm{CTF},
$$

and this is exactly where many first encounters with real micrographs become emotionally rough. Once this equation clicks, you realize that the microscope does not simply record structure. It reshapes frequency content before you ever see the image.

That is why raw cryo-EM images can look low-contrast, partly inverted, or just confusing at first glance. CTF zero crossings remove information at specific frequencies. Oscillations can flip contrast. Envelope terms damp high-frequency detail. So two images of the same object can look surprisingly different under different settings.

Now add dose limits. We cannot blast fragile biological samples with unlimited electrons, so we operate in a low-dose regime where single-image SNR is poor. The hard combination is this: CTF weakens part of the frequency content first, then noise further obscures what remains. This is not a failure of interpretation skill. It is the native operating condition of the experiment.

This is also why averaging and inference are so important later. You do not recover structure by finding one magical image. You recover it by combining many transfer-modulated, noisy views in a physically consistent way.

At this stage, it is worth sanity-checking your intuition: why can a sharper-looking image still miss crucial frequencies, why does changing defocus move information loss across frequency bands, and why is low-dose imaging not optional in cryo-EM? If those three questions feel answerable in your own words, you are in a very good place for the final section.

You now have the right expectation: a single cryo image is noisy and transfer-modulated by design, not by accident. Next we close Chapter 2 by connecting all this to SPA workflow, sample preparation, and conformational heterogeneity.
