Us personally, we loved the previous two widgets. There’s just something very satisfying about watching a neural network try to predict whether a cat is standing or lying down. It’s almost bordering on the absurd; the amount of compute we spent on training these models on our own laptops overnight must be the equivalent of supercomputers just a few decades ago. And now we can ever so casually watch a machine struggle with cat pictures…

Continuing the struggle, what do we have to say about internal validation? Remember, that was the part where we would like to test whether our learned neural posterior estimator accurately captures the simulated training dataset (not whether it’s actually ‘realistic’). This leads us to a neat concept called _Simulation Based Calibration_ (SBC). Don’t be fooled by the name, this method does not make our model well calibrated it just gives us information _whether_ we are.

Here’s the "mantra" behind SBC you should remember:

### The true parameter $\theta^*$ should look like any other sample drawn from the simulated posterior.

This statement needs some unpacking; it’s something we struggled a lot for some reason.

Consider a fixed observation $x$. There exists a **true posterior**

$$
p^*(\theta \mid x),
$$

and our model learns an approximation

$$
q(\theta \mid x).
$$

Now suppose we generate an observation $x_{\text{sim}}$ using a ground-truth parameter $\theta^*$.

Crucially, this $\theta^*$ is not special. It is simply one draw from the true posterior $p^*(\theta \mid x_{\text{sim}})$.

If our model has learned the posterior correctly, then samples

$$
\theta \sim q(\theta \mid x_{\text{sim}})
$$

should be statistically indistinguishable from samples drawn from the true posterior.

In other words:

> **$\theta^*$ should “look like” any other sample from the posterior.**

How do we make this idea quantitative?

The simplest way is to compare $\theta^*$ to samples from the estimated posterior. Concretely, we draw many samples $\theta$ from $q(\theta \mid x_{\text{sim}})$ and ask:

> _How many of these samples are smaller than $\theta^_$?\*

This number is called the **rank** of $\theta^*$. If $\theta^*$ truly behaves like a typical sample from the posterior, then its rank should also behave like that of any other sample.

A random sample from a distribution will sometimes lie in the left tail, sometimes near the center, and sometimes in the right tail. Consequently, over many repeated experiments, the rank of $\theta^*$ should be **uniformly distributed**.

To verify this, we repeat the experiment many times and plot a histogram of the resulting ranks:

- If the histogram is **uniform**, the model is well-calibrated.
- If it is not, the model is systematically wrong (e.g., overconfident or biased).

You can explore this for yourself:

[sbi theory widget]
