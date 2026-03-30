### Applying Simulation-Based Calibration (Rank Statistics) to our own data

Now that we have a grasp on one potential method to check if our model is consistent with our simulated data, we can apply this knowledge to our own cat-conformation inference model.

What would the equivalent of a “single trial” from the previous explainer be for our case?

- Step 1: Sample the “True” Parameter $\theta^*$ from the exact same distribution used during training, e.g., uniform across all possible model indices. Crucially: Even though we only care about the rank of the Conformation Index, we must still sample all nuisance parameters (like random rotations and noise levels) from their respective priors to simulate a realistic image that matches the model’s training experience.

- Step 2: Feed our sampled $\theta^*$ and nuisance parameters into our CryoEM simulator. This generates a noisy 2D projection: our experimental data $x_{sim}$ for this trial. An interesting experiment is to slightly alter the settings used to generate projections (e.g., increase their noise or slightly change imaging parameters) to test the model’s robustness under deliberate misspecification. This blurs the boundaries of purely internal validation but is informative nonetheless.

- Step 3: Pass the simulated image $x_{sim}$ into the trained estimator. Ask it to generate $M$ samples (e.g., 50 or 100) from the estimated posterior.

- Step 4: Count how many of the M predicted samples are smaller than the original “true” $\theta^\*$. This integer is your rank statistic for this trial.

By repeating these 4 steps $N$ times, we can build the histogram and ECDF plots shown on the previous page to see if our cat-model is genuinely "honest" about its conformational uncertainty. Here, $N$ is the number of individual trials we perform. A rough guideline for choosing a large enough $N$ is to ensure your rank histogram stays stable if you repeat the entire calculation. Stability implies you've sampled a sufficiently large volume of your priors (orientation, noise, CTF, etc.) to obtain a broadly representative sample.

Using the methods just covered, we can explore how our pre-trained models perform:

Let's see this in action in the next interactive widget:
