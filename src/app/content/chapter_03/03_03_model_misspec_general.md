### Model Misspecification

Here, we need to acknowledge that SBI works only as well as the simulator represents reality. This limitation is often called the simulation gap and remains an active research challenge.

Furthermore, we must critically assess whether the learned model is reliable. If the learned posterior is systematically biased, this is a form of model misspecification.

It is useful to separate those two criteria. _Internal_ validation asks whether the estimator learned the simulated distribution well. _External_ validation asks whether simulation itself is close enough to reality for scientific use. Good performance on the synthetic training set alone does not guarantee good real-world inference.

In our case study, a model can perform excellently on held-out synthetic images yet fail on real measurements if critical physical effects are missing or poorly calibrated in the simulator.

Let’s first explore a form of external validation; ideally you would be using real world experimental data to test against but we could not procure access to a cat-friendly cryo electron microscope in time. Thus we opted to test how well our models perform when inferring on images where the imaging parameters (remember the CTF?) have changed, as compared to the training set. You can even test this yourself in the following widget. You are now given control of the imaging parameters for the picture in the right box. You can then check how the inferred posteriors change, if you hit the model with images with parameters it has not seen during training.

First, we do a superficial test. That is, visually compare the distribution of generated and true images by "inspection". As these are incredibly high-dimensional for images, we need to do it via dimensionality reduction, and chose UMAP as in the original paper, a well known technique. As this is not the only, nor the best way, we use a more mathematically and statistically robust technique. A well established way of comparing the distributions is Maximum Mean Discrepancy (MMD), where we test whether two independent sets of samples come from two different distributions by applying a Gaussian kernel between to samples and compute Euclidian distance.
