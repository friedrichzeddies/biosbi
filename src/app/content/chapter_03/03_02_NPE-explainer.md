### But what is our Density Estimator?

SBI is not tied to a single posterior-estimator architecture; several families are possible. However, many classical posterior methods either require an explicit likelihood or are computationally very expensive, and in the worst case both. A strong practical option is **Normalizing Flows** (NFs), which are flexible density estimators and therefore a natural focus for this project.

### Interlude: Normalizing Flows

Rather than directly trying to model a complicated distribution over parameters, NFs take a more indirect, yet very powerful route.
The core idea can be summarized as follows:

> Start from a simple distribution (e.g. a Gaussian) and transform it step by step into a complex one.

Each step of the process should be fast to compute and invertible. Because each transformation is invertible, we can keep track of how probability mass changes under these transformations. This is crucial: it allows us to evaluate the resulting density $q(\theta)$ exactly, rather than just sampling from it.

The true posterior $p(\theta \mid x)$ can have a very complicated shape:

- it may be multi-modal (several plausible solutions),
- skewed,
- or have strong correlations between parameters.

Simple distributions (like Gaussians) cannot capture this structure well. Normalizing flows, on the other hand, can approximate arbitrarily complex distributions by composing enough transformations.

In the context of SBI, we make each ‘step’ conditional on the observation:
This means:

- the transformation itself depends on the input image x,
- different observations lead to different posterior shapes.

Intuitively, the model learns:

_“Given this image, how do I need to warp a simple Gaussian to represent all plausible parameters?”_

**What to take away from the last section:**

- SBI reduces inference to learning a mapping from observations (e.g. projection images of cats) to distributions over explanatory parameters (e.g. conformations of said cat).
- Normalizing Flows provide a powerful way to represent these distributions and to explicitly evaluate their probability density.
- The combination allows us to approximate posteriors that would otherwise be intractable.

### Back to SBI: The Training

Let's just get a few words out of the way, which are often thrown around:

**"Joint training"** - We train the feature-extraction network and conditional estimator with standard optimization methods. Importantly, both networks are trained jointly, ensuring that the learned features are directly optimized for the posterior estimation task rather than for generic image representation.

**"Run by simulation"** - Once we fix priors over plausible explanatory variables, the simulator continuously generates training pairs and we use them to optimize the neural posterior estimator. Training typically uses many independent mini-batches; we do not store every sample explicitly, but their information is absorbed into model weights. Post-training visualizations should therefore be interpreted as examples, not exact substitutes for the full training distribution, although they will on average display the same behavior as the random generation is independent at all times.

### Inference

With our trained model ready, we can finally perform inference on experimental observations. The procedure is straightforward: the estimator receives an observation and returns plausible parameter values together with calibrated uncertainty.

This is where the fun begins! In the following widget, you can create simulated electron-microscopy images of cats in different projections and see their computed posterior distributions, as well as the assigned probabilities of which conformation the cat is in. You can truly spend quite a lot of time playing around here, and we certainly have. We've put a collapsible box beneath the widget that explores some of our favorite things to do! If you cannot see a cat, make sure to toggle the ‘Show clean density’ box.
