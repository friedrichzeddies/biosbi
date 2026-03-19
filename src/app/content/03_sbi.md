## Simulation-Based Inference (SBI)

### Why SBI exists

Simulation-Based Inference (SBI) is a framework for Bayesian inference in settings where we can simulate data, but cannot write down a tractable likelihood function. This situation is common in modern science: the forward process is known well enough to generate synthetic observations, yet the exact probability density $p(x\mid\theta)$ is too complex to evaluate directly.

Having explored cryo-EM theory in the previous chapter, we can now use it as a concrete example for SBI. We will first introduce SBI as a stand-alone concept and then repeatedly connect each idea back to cryo-EM.

### The core problem: forward is easy, inverse is hard

Most scientific models are naturally written in forward form. We choose parameters $\theta$, run a simulator, and obtain an observation $x$. Conceptually, this is the map

$$
x = f(\theta).
$$

In practice and experiments, however, the scientific question is usually inverse: after measuring $x_{obs}$, which parameter values are plausible? Formally, we want the posterior

$$
p(\theta\mid x_{obs}).
$$

Consider our core cryo-EM question: "Which conformations are plausible given the image we measure in an experiment?" This is an inverse task based on real experimental data.
However, the forward simulator generates an image from structural and imaging _parameters_. The inverse task is to infer which structures and conditions are compatible with a measured micrograph or object image from the simulation.

As the true likelihood is unavailable, classical likelihood-based Bayesian workflows are difficult or impossible to apply directly. SBI closes this gap by learning the inverse relation from simulated pairs $(\theta_i, x_i)$.

In our context, this means we train on simulated images and then use the learned posterior surrogate to infer parameters for real experimental data.

### Variable formalism and prior knowledge

Now is a good time to formalize the variables we have been using implicitly. We observe an image, denoted by $x_{obs}$, which is an **Observable Variable**. Although observable variables are measurable, they are not our primary target. Instead, we seek the underlying configurations, here our _parameters_ $\theta$, called **Explanatory Variables**.

Because SBI is Bayesian, prior information matters. Before simulation starts, we specify which parameter values (or ranges) are plausible. In addition to explanatory variables, we also include **Nuisance Variables** that affect observations but are not the primary object of interest.

In a simplified notation, one can think of a simulator sampling

$$
(\theta, \eta, x) \sim p(\theta)\,p(\eta)\,p(x\mid\theta,\eta).
$$

and then learning to recover information about $\theta$ from $x$. Including nuisance variation during simulation is essential, because it teaches the model to distinguish robust signal from incidental variability.

Remember our step-by-step theory reconstruction in the previous chapter: nuisance factors included noise level, imaging conditions such as lens aberrations (introducing the CTF), and orientation effects. If these are not represented realistically in simulation, posterior estimates can become overconfident. The conditional $p(x\mid\theta,\eta)$ can also be deterministic, for example when the simulator is a deterministic mapping plus fixed settings.

### The statistical object SBI learns

As indicated above, SBI methods train neural estimators on simulated data. Depending on the method family, one may learn a posterior, a likelihood surrogate, or a likelihood ratio. A common target is direct posterior estimation,

$$
q(\theta\mid x) \approx p(\theta\mid x),
$$

where $q$ is a neural density estimator. After training, inference for a new **observation** can be very fast.

This is a key conceptual shift: instead of solving a fresh inverse problem from scratch for every new observation, we spend computation once during training and reuse it many times later. This is called _amortized inference_.

In our example in cryo-EM, concretely, this means after training on large batches of synthetic images (from the forward simulation), the model can return a posterior for each newly acquired image without rerunning expensive sampling pipelines from zero.

After a few more core ideas we will come back to the exact implementation of this. But first, ...

### ... why posteriors are better than point estimates

A point estimate answers: "What is one plausible parameter value?" A posterior answers: "Which values are plausible, and with what uncertainty?" For inverse problems that are ambiguous or ill-posed, this distinction is critical.

If multiple parameter settings can explain nearly the same observation, the posterior should represent that ambiguity explicitly. This makes scientific interpretation safer and more honest, especially when downstream decisions depend on uncertainty.

This can be illustrated by our cat example: a cat lying down and a cat standing, both seen from the top, can produce very similar projections, potentially indistinguishable once noise is added. Yet the underlying states are different. More generally (and applicable to proteins), different conformations or orientations may produce similar image evidence. A posterior can represent this multi-modality, while a single estimate can hide it.

### A practical SBI workflow

In practice, SBI is often organized in two stages. In a simulation stage, we generate many synthetic samples and train the estimator. In an inference stage, we evaluate the trained estimator on real observations and obtain posterior predictions. The simulation stage may be computationally heavy, but it is usually cheaper and more scalable than collecting equivalent real data.

In our usecase, microscope time (or possibly a multi-million dollar acquisition) and sample preparation are expensive and time consuming, whereas large-scale simulation can run on compute infrastructure. In this project, simulations are relatively cheap because they rely on random sampling and comparatively simple image-generation steps. SBI exploits this asymmetry by shifting effort from costly data acquisition to scalable computation.

#### Images are of large dimension

Our data are images, not small tuples such as energies or coordinates, so the input dimension is large even at low resolution. This matters for two reasons. First, high-dimensional inputs increase computational cost. Second, not every pixel is equally informative; many pixels contribute little to parameter recovery. To address this, we use **summary networks** $h$ that extract compact and informative features,

$$
s = h(x).
$$

These summaries serve as learned preprocessing for posterior estimation. A common architecture is ResNet, which can be scaled to different compute and expressivity requirements.

[List of paper arcitectures? Implementation of input through a summary net might be pedagocial / gives intuition?]

#### But what is our Density Estimator?

SBI is not tied to a single posterior-estimator architecture; several families are possible. However, many classical posterior methods either require an explicit likelihood or are computationally very expensive, and in the worst case both. A strong practical option is **Normalizing Flows** (NFs), which are flexible density estimators and therefore a natural focus for this project.

#### WIP - Interlude: Normalizing Flows

[Get deep into NF territory?]

- Pros:
  - Nice to have für Prof.
  - Is "free content"

- Cons:
  - Pretty large topic
  - Not really interactive right?

Alternative: Really basic, just a few sentences / paragraphs and images as well as the list of usable NF sub-architectures.

TL;DR: "$q$" that builds conditional estimator to build surrogate of posterior.

#### Back to SBI: The Training

**"Joint training"** - Now that we know what can be tuned, we train the feature-extraction network and conditional estimator with standard optimization methods. Importantly, both networks are trained jointly %why tho?%

**"Run by simulation"** - once we fix priors over plausible explanatory variables, the simulator continuously generates training pairs and we use them to optimize the neural posterior estimator. Training typically uses many independent mini-batches; we do not store every sample explicitly, but their information is absorbed into model weights. Post-training visualizations should therefore be interpreted as examples, not exact substitutes for the full training distribution, although they will on average display the same behavior as the random generation is independent at all times.

[Training plots / Results? Display, but not really interactive right?]

### Inference

With our trained model ready, we can perform inference on experimental observations. The procedure is straightforward: the estimator receives an observation and returns plausible parameter values together with calibrated uncertainty.

[Possible interaction in this chapter

vary one component at a time and observe how the posterior changes:

(1. Adjust selected simulation parameters and inspect the resulting synthetic image. | we did that but it might be a worthy reuse of the code here ^^) 2. Run inference on that image (or a real measurement?) and inspect posterior shape, spread, and possible multi-modality. 3. Deliberately introduce mismatch (for example altered noise or optics settings) to illustrate model misspecification effects.]

### Model Misspecification

First, we need to acknowledge that SBI works only as well as the simulator represents reality. This limitation is often called the simulation gap and remains an active research challenge.

Furthermore, we must critically assess whether the learned model is reliable. If the learned posterior is systematically biased, this is a form of model misspecification.

It is useful to separate two validation questions. Internal validation asks whether the estimator learned the simulated distribution well. External validation asks whether simulation itself is close enough to reality for scientific use. Good training performance alone does not guarantee good real-world inference.

In our case study, a model can perform excellently on held-out synthetic images yet fail on real measurements if critical physical effects are missing or poorly calibrated in the simulator.

%Note: I am not sure how exactly the model misspecification is divided in internal and exteranal validation in the paper and how we would implement it concretely (internal: Using generated image, is the posterior good makes sense in paper and our case, but external: true distribution unknown, so they use a well known example? What do we do with our cat as real distribution wont be possible either?). Here some more text needs to be added!

### Brief Summary on SBI

SBI is a rigorous response to a common scientific regime: simulator available, likelihood intractable, inverse inference required. Its core strengths are Bayesian uncertainty quantification, amortized inference, and direct use of mechanistic domain knowledge through simulation.

Cryo-EM is a natural example of this regime, but the conceptual framework is broader. In compact form: simulate forward, learn inverse, and validate carefully. This is the logic we could specialize to cryo-EM.
