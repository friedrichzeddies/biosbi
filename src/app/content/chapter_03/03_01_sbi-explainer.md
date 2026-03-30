## Simulation-Based Inference (SBI)

### Why SBI exists

Simulation-Based Inference (SBI) is a framework for Bayesian inference in settings where we can simulate data, but cannot write down a tractable likelihood function. This situation is common in modern science: the forward process is known well enough to generate synthetic observations, yet the exact probability density $p(x\mid\theta)$ is too complex to evaluate directly. If you are not familiar with the vocabulary of Bayesian statistics, don’t worry! We’ll get you right on track using our cats as an example from which we can generalise.

### The core problem: forward is easy, inverse is hard

Most scientific models are naturally written in forward form. That’s because we often have a good grasp of cause and effect in physical systems. If you throw a ball and know its position and velocity, you can calculate where it will land under certain assumptions. Throw it at a different angle or speed and it will land somewhere else. The same can be said for our electron microscope. After thoroughly exploring the image formation process, we have a very good idea of how a given 3D structure in some orientation will produce an image. We know it will be a projection whose Fourier spectrum is multiplied by the CTF before being Fourier-transformed back, after which noise is added. This can be generalized to many systems; you break down complex processes into discrete steps that you can describe mathematically. The following is the kind of vocabulary often used to describe such _forward models_:

Given some parameters $\theta$ as input to a forward model, we obtain an observation $x$. Conceptually, this defines the map

$$
x_{obs} = f_{obs}(\theta).
$$

Producing an observation given some input parameters is generally a probabilistic process, hence we often choose to describe it as a probability distribution. In real electron microscopy, numerous factors add randomness to any given observation: thermal fluctuations, vacuum pressure variations, stray magnetic fields, and so on.

In practice and experiments, however, the primary scientific question is usually aimed in the inverse direction: “After measuring $x_{obs}$, which parameter values $\theta$ are plausible?”. We can translate this question back to our example: “Given an image of a projection, can we deduce whether the cat is standing, lying down, or something in between?”. Formally, we want to find the posterior distribution

$$
p(\theta\mid x_{obs}).
$$

In this case, _posterior_ is the statistical term for the probability distribution of parameters (e.g., its conformation) given an observation. Learning about unknown quantities from data is generally called _inference_, hence the 'I' in SBI. Furthermore, inverting a known forward process (such as a simulation) is called solving an _inverse problem_. This can be a daunting mathematical task, but SBI is an elegant way to approach it:

If we understand the underlying forward process (e.g., electron microscopy) well enough to build a convincing\* simulator (a computer program that takes in parameters $\theta$ and outputs synthetic observations $x_{sim}$), we can generate pairs of observations and the parameters that produced them $\{x_{sim}, \theta \}$. Note that this would be extremely difficult to do with the "real" physical process because, most of the time, we do not know the underlying exact true parameters that produced a specific experimental observation.

\*_we’ll get into what convincing means later on_

As a tangent: Understanding simulations in this framework, we note that this often runs counter to the general usage of the word “simulation”. In everyday life, we often reserve this term only for the deterministic case. When somebody claims that “life is a simulation” they most probably want to convey that everything is already pre-computed and free will doesn’t exist.
In most scientific models (such as simulating electron microscopy images) we do not constrict ourselves to the deterministic version of simulators. That’s because we know that the real world is messy and noisy so we build randomness, often via noise, into our simulations. Just like we have done for our simple EM-model. There are often many other avenues of non-deterministic behaviour but noise is intuitive enough to suffice as an example.
Let’s get back to our main quest: solving an inverse problem.

This abundance of labeled training data $\{x_{sim}, \theta \}$ is exactly the key. With enough training data, we have a solid chance of inferring the complex statistical relationship between the synthetic observations and the parameters used to produce them.

At this point you might ask yourself: “Why do we need so much data if we already have a convincing simulation of the real forward-process?”. The key insight here is that most simulations (whether simulating image formation for cryo-EM, fluid dynamics for weather prediction, or disease spreading in a population) take parameters $\theta$ as an input and output a single observation $x_{sim}$ that is _compatible_ with the parameters. But by themselves, they do not reveal how mathematically likely this specific observation is. Your simulation could have sampled a highly unlikely edge-case observation (e.g., all noise in the image randomly happened to cancel out). The question about how likely a given observation $x_{sim}$ is regarding the parameters remains unanswered. SBI side-steps this problem by using massive datasets of paired $\{x_{sim}, \theta \}$ to directly learn the underlying statistics.

### Variable formalism and prior knowledge

Now is a good time to formalize the variables we have been using implicitly. We observe an image, denoted by $x_{obs}$, which is an **Observable Variable**. Although observable variables are measurable, they are not our primary target. Instead, we seek the underlying configurations, here our _parameters_ $\theta$, called **Explanatory Variables**.

Because SBI is Bayesian, prior information matters. Before simulation starts, we specify which parameter values (or ranges) are plausible. In addition to explanatory variables, we also include **Nuisance Variables** that affect observations but are not the primary object of interest.

In a simplified notation, one can think of a simulator sampling

$$
(\theta, \eta, x) \sim p(\theta)\,p(\eta)\,p(x\mid\theta,\eta).
$$

Including nuisance variation during simulation is essential, because it teaches the model to distinguish robust signal from noise or other factors we are not interested in.

Recall our step-by-step explanation of image formation in cryo-EM from the previous chapter: nuisance factors included the noise level, imaging conditions such as lens aberrations (remember the CTF?), and projection orientations. If these are not represented realistically in the simulation, the posterior estimates can become dangerously misguided.

#### A Critical Comment

Here we should also mention, that prior knowledge has a significant caveat: We also need to have a good guess or knowledge about the object or structure before we have actually _seen_ it. In our toymodel, we are not constrained at all, as we know our cat. In structural biology, that is generally not the case. The quality of this whole approach heavily depends on what we already know and our simulation will be bad if we know only little.

However, we can mitigate this with two approaches, we know that the structure is related to one that is already well-enough reconstructed, or we use biochemical knowledge to simulate priors to start from with up and coming computational methods (e.g. AlphaFold).

### The statistical object SBI learns

As indicated above, SBI methods train neural estimators on simulated data. A common target is direct posterior estimation $p(\theta \mid x)$ from the many simulated pairs $(x_{sim}, \theta)$. Remember, the posterior is a probability distribution in parameter space that mathematically describes how well a given parameter $\theta$ explains the observation $x$. In Neural Posterior Estimation (_NPE_), we learn to directly estimate this posterior:

$$
q(\theta\mid x) \approx p(\theta\mid x),
$$

where $q$ is a neural density estimator. The network is trained using maximum likelihood: we adjust its parameters so that the simulated parameters $\theta$ are as likely as possible given their corresponding observations $x_\text{sim}$.

After training, inference for a new **observation** can be very fast, e.g. understanding what parameters explain the new observation.

This is a key conceptual shift: instead of solving a fresh inverse problem from scratch for every new observation, we spend computation once during training and reuse it many times later. This is called _amortized inference_.

In our example in cryo-EM, concretely, this means after training on large batches of synthetic images (from the forward simulation), the model can return a posterior for each newly acquired image without rerunning expensive sampling pipelines from zero.

After a few more core ideas we will come back to the exact implementation of this. But first, ...

### ... why posteriors are better than point estimates

A point estimate answers: "What is one plausible parameter value?" A posterior answers: "Which values are plausible, and with what uncertainty?" For inverse problems that are ambiguous or ill-posed, this distinction is critical.

If multiple parameter settings can explain nearly the same observation, the posterior should represent that ambiguity explicitly. This makes scientific interpretation safer and more honest, especially when downstream decisions depend on uncertainty.

This can be illustrated by our cat example: a cat lying down and a cat standing, both seen from the top, can produce very similar projections, potentially indistinguishable once noise is added. Yet the underlying states are different. More generally (and applicable to proteins), different conformations or orientations may produce similar image evidence. A posterior can represent this multi-modality, while a single estimate can hide it.

We ourselves have trained a few models on cats in different conformations. Below, you may check out the cat we used as our model of choice:
