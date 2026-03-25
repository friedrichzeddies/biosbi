# Applying Simulation Based Calibration (Rank Statistics) for our own data
Now that we have a grasp on one potential method of checking if our model is consistent with our simulated data we can apply this newfound knowledge to our very own cat-conformation-model.

What would the equivalent of a 'single trial' from the above explainer be for our case?

In the `cryo_sbi` module, the "parameter" vector $\theta$ actually contains several variables (rotation, shift, defocus, etc.), but our NPE model is specifically trained to predict the **Conformation Index**. 

- **Step 1: Sample the "True" Parameter $\theta^*$.** 
  To run a valid SBC trial, you must draw your "true" parameter from the exact same distribution used during training. In our code, this is the `index_prior` found in `cryo_sbi/inference/priors.py`. This prior is a `BoxUniform` distribution ranging from 0 to the number of conformations minus 1. 
  
  *Crucially*: Even though we only care about the rank of the index, we must still sample all "nuisance parameters" (like random rotations and noise levels) from their respective priors to simulate a realistic image that matches the model's training experience.

- **Step 2: Simulate the Observation $x$.**
  Feed your sampled $\theta^*$ and nuisance parameters into the `CryoEmSimulator`. This generates a noisy 2D projection—our "experimental data" for this trial.

- **Step 3: Draw Posterior Samples $\tilde{\theta}$.**
  Pass the simulated image $x$ into the trained `estimator`. Ask it to generate $M$ samples (e.g., 50 or 100). These samples represent the model's "guess" at which conformation produced that image.

- **Step 4: Calculate the Rank.**
  Count how many of the $M$ predicted samples are smaller than your original "true" $\theta^*$. This integer is your Rank Statistic for this trial.

By repeating these 4 steps $N$ times, we can build the histogram/ECDF plots from the previous page to see if our cat-model is actually "honest" about its conformational uncertainty. Here, $N$ is how many individual trials we do. A rough guideline as to what is a big enough N is to make sure that your rank histogram stays stable if you repeat the whole calculation. That means you've sampled from a well enough covered volume of your priors (orientation, noise, CTF etc.) to have a, to first order, representative sample

Let's see this in action in the next interactive widget: