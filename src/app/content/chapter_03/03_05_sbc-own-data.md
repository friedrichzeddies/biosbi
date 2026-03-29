### Applying Simulation Based Calibration (Rank Statistics) for our own data

Now that we have a grasp on one potential method to check if our model is consistent with our simulated data, we can apply this knowledge to our own cat-conformation-checking model.

What would the equivalent of a “single trial” from the previous explainer be for our case?

- Step 1: Sample the “True” Parameter $\theta^*$ from the exact same distribution used during training, e.g., uniform across all possible model indices. Crucially: Even though we only care about the rank of the Conformation Index, we must still sample all nuisance parameters (like random rotations and noise levels) from their respective priors to simulate a realistic image that matches the model’s training experience.

- Step 2: Feed our sampled $\theta^*$ and nuisance parameters into our CryoEM simulator. This generates a noisy 2D projection: our experimental data $x_{sim}$ for this trial. An interesting experiment is to slightly alter the settings used to generate projections (e.g., increase their noise or slightly change imaging parameters) to test the model’s robustness under deliberate misspecification. This blurs the boundaries of purely internal validation but is informative nonetheless.

- Step 3: Pass the simulated image $x_{sim}$ into the trained estimator. Ask it to generate $M$ samples (e.g., 50 or 100) from the estimated posterior.

- Step 4: Count how many of the M predicted samples are smaller than the original “true” \theta^\*. This integer is your rank statistic for this trial.

By repeating these 4 steps $N$ times, we can build the histogram/ECDF plots from the previous page to see if our cat-model is actually "honest" about its conformational uncertainty. Here, $N$ is how many individual trials we do. A rough guideline as to what is a big enough $N$ is to make sure that your rank histogram stays stable if you repeat the whole calculation. That means you've sampled from a well enough covered volume of your priors (orientation, noise, CTF etc.) to have a, to first order, representative sample.

Using the methods just covered, we can explore how our pre-trained models perform:

Let's see this in action in the next interactive widget:

<!-- TODO(widget): Display SBI own-data widget here. -->
