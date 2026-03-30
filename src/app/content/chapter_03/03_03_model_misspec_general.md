### Model Misspecification

Here, we need to acknowledge that SBI works only as well as the simulator represents reality. This limitation is often called the simulation gap and remains an active research challenge.

Furthermore, we must critically assess whether the learned model is reliable. If the learned posterior is systematically biased, this is a form of model misspecification.

It is useful to separate those two criteria. _Internal_ validation asks whether the estimator learned the simulated distribution well. _External_ validation asks whether simulation itself is close enough to reality for scientific use. Good performance on the synthetic training set alone does not guarantee good real-world inference.

In our case study, a model can perform excellently on held-out synthetic images yet fail on real measurements if critical physical effects are missing or poorly calibrated in the simulator.

Let’s first explore a form of external validation. Ideally, you would use real-world experimental data to test against, but we could not procure access to a cat-friendly cryo-electron microscope in time. Therefore, we opted to test how well our models perform when inferring on images where the imaging parameters (remember the CTF?) are deliberately altered compared to the training set. You can test this yourself in the following widget. You are given control of the imaging parameters for the picture in the right box. You can then observe how the inferred posteriors behave when you hit the model with images generated from parameters it has never seen during training.

First, we perform a superficial test: visually comparing the distribution of generated and true images by 'inspection.' Because images are incredibly high-dimensional, we must do this via dimensionality reduction; we chose UMAP (as in the original paper), a well-known technique. However, since visual inspection is neither the only nor the most rigorous method, we also use a more mathematically and statistically robust technique. A well-established way of rigorously comparing distributions is Maximum Mean Discrepancy (MMD), where we test whether two independent sets of samples come from the same distribution by applying a kernel between the samples and computing their statistical distance.
