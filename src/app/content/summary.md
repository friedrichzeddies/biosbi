## Summary

That was a lot of content, no question. But if you zoom out, it all follows one clean thread from beginning to end. We began by understanding how cryo-EM images are physically generated, identified what information is distorted or lost. We then aimed to infer some learnable parameters (e.g. conformation) using uncertainty-aware Bayesian methods in an SBI framework, such as Neural Posterior Estimation. We explored how to validate and test such models as well as just playing around with them.

## The Story Revisted

- Electron Microscpy produces very noisy, CTF-affacted projection images of particles in random orientations and conformations. We know very well how to simulate the forward process because it's _all diffraction_. 

- This naturally motivates SBI: Forward simulation is feasible, exact likelihoods are not, so we learn posteriors from simulated data. We can generate a large synthetic training sets of images and their corresponding conformations.

- For high-dimensional images, representation learning (for example ResNet summaries) first compresses observations. Then we learn a Neural Posterior Estimate 
(in form of a Normalizing Flow) to infer a plausible conformation given a new image based on what we have seen in training.

- We try to valididate or disprove that the model learned the correct conditional posteriors. We test whether the model learned the simulated training distribution well and also whether the simulated training distribution is close enough to real data.

### Final Takeaway
We are aware that, after this short course, you will not yet be able to implement such models on your own — but that was never the goal. If this is your first time encountering these ideas, we hope it felt like an inviting introduction rather than something overwhelming. And if you already had some familiarity, we hope that the opportunity to interactively explore these concepts offered a fresh perspective, and perhaps even a bit of fun along the way.

We hope you now see both cryo-EM physics and SBI from a more intuitive perspective and feel confident transferring these concepts to other domains. And if you are curious to go further, we would be very happy if you try the original source code with actual proteins and explore where your own questions lead.

Thank you for participating, and until we meet again.

Sebi and Friedel
