## Simulation-Based Inference (SBI)

### Why SBI exists

Simulation-Based Inference (SBI) is a framework for Bayesian inference in settings where we can simulate data, but cannot write down a tractable likelihood function. This situation is common in modern science: the forward process is known well enough to generate synthetic observations, yet the exact probability density $p(x\mid\theta)$ is too complex to evaluate directly. If you are not familiar with the vocabulary of Bayesian statistics, don’t worry! We’ll get you right on track using our cats as an example from which we can generalise.

### The core problem: forward is easy, inverse is hard

Most scientific models are naturally written in forward form. That’s because we often have a good grasp on cause and effects in physical systems. If you throw a ball and you know its position and velocity you can calculate where it will land, under some assumptions. Throw it at a different angle or speed and it will land somewhere else. The same can be said for our electron microscope. After we have thoroughly explored the image formation process, we have a really good idea of how a given 3D structure in some orientation will produce an image. We know it will be a projection whose Fourier Spectrum is multiplied by the CTF before being fourier-transformed back and then noise is added. This can be generalised to many systems; you break down complex processes into steps which you can describe well. The following is the kind of vocabulary often used to describe such _forward models_:

Given some parameters $\theta$ as input to a forward model, we obtain an observation $x$. Conceptually, this defines the map

$$
x_{obs} = f_{obs}(\theta).
$$

Producing an observation, given some input parameters, is generally a probabilistic process, hence we often chose to describe it as a probability distribution. In real electron microscopy, many things add randomness to any given observation; thermal fluctuation, pressure, stray magnetic fields and so on. 

In practice and experiments, however, the scientific question is usually along the inverse direction: “After measuring $x_{obs}$, which parameter values $\theta$ are plausible?". We can translate this question back to our example: “Given some image of its projection, can we deduce whether the cat is standing, lying down, or something in between?”. Formally, we want the posterior distribution

$$
p(\theta\mid x_{obs}).
$$

In this case, _posterior_ is the fancy word for the probability distribution of parameters (e.g. its conformation) given some observation. Learning about unknown quantities from data is generally called _inference_, hence the I in SBI. Furthermore, if we want to invert a known forward process (such as a simulation) this is called an _inverse problem_. This is a daunting task. But SBI is one way to approach it:

If we understand the underlying forward process (e.g. electron microscopy) well enough to build a convincing* simulator (a computer program which takes in parameters $\theta$ and outputs convincing observations $x_{obs}$), we could generate pairs of convincing observations and the parameters which produced them $\{x_{obs}, \theta \}$. Note that this would be very hard to do with the "real" forward process because most of the time we do not know the underlying set of parameters which produced a specific observation.

*_we’ll get into what convincing means later on_


As a tangent: Understanding simulations in this framework, we note that this often runs counter to the general usage of the word “simulation”. In everyday life, we often reserve this term only for the deterministic case. When somebody claims that “life is a simulation” they most probably want to convey that everything is already pre-computed and free will doesn’t exist.
In most scientific models (such as simulating electron microscopy images) we do not constrict ourselves to the deterministic version of simulators. That’s because we know that the real world is messy and noisy so we build randomness, often via noise, into our simulations. Just like we have done for our simple EM-model. There are often many other avenues of non-deterministic behaviour but noise is intuitive enough to suffice as an example. 
Let’s get back to our main quest: solving an inverse problem.

It is the abundance of labelled training data $\{x_{obs}, \theta \} which is key. If we have enough training data, we might have a shot of inferring the statistical relationship between (synthetic yet convincing)  observations and the parameters used to produce them.

At this point you might ask yourself: “Why do we need so much data if we already have a convincing simulation of a real forward-process?”. Well, the key insight here is that most simulations (image formation for our CryoEM example, fluid simulations for weather prediction, spreading of disease in a population etc.) take parameters $\theta$ as an input and output a single observation $x_{sim}$ which is _compatible_ with the parameters. But by itself, they do not give you the information of how likely this observation is. Your simulation could have sampled quite an unlikely observation (all noise in the image just happened to be zero). The question about how likely a given observation $x_{sim}$ is in regards to the parameters which could be used remains unanswered. SBI side-steps this problem by using many pairs of $\{x_{obs}, \theta \} to directly learn the underlying statistics. 

### Variable formalism and prior knowledge

Now is a good time to formalize the variables we have been using implicitly. We observe an image, denoted by $x_{obs}$, which is an **Observable Variable**. Although observable variables are measurable, they are not our primary target. Instead, we seek the underlying configurations, here our _parameters_ $\theta$, called **Explanatory Variables**.

Because SBI is Bayesian, prior information matters. Before simulation starts, we specify which parameter values (or ranges) are plausible. In addition to explanatory variables, we also include **Nuisance Variables** that affect observations but are not the primary object of interest.

In a simplified notation, one can think of a simulator sampling

$$
(\theta, \eta, x) \sim p(\theta)\,p(\eta)\,p(x\mid\theta,\eta).
$$

Including nuisance variation during simulation is essential, because it teaches the model to distinguish robust signal from noise or other factors we are not interested in.

Remember our step-by-step instruction how image formation works in CryoEM from in the previous chapter: nuisance factors included noise level, imaging conditions such as lens aberrations (remember the CTF?), and orientation. If these are not represented realistically in simulation, posterior estimates can become misguided.

### The statistical object SBI learns

As indicated above, SBI methods train neural estimators on simulated data. A common target is direct posterior estimation $p(\theta | x)$ from the many simulated pairs $(x_{sim}, \theta)$. Remember, the posterior is a probability distribution in parameter space which describes how well a given parameter $\theta$ explains the observation $x$. In Neural Posterior Observation (_NPE_) we learn to directly estimate this posterior:

$$
q(\theta\mid x) \approx p(\theta\mid x),
$$

where $q$ is a neural density estimator. After training, inference for a new **observation** can be very fast, e.g. understanding what parameters explain the new observation. 

This is a key conceptual shift: instead of solving a fresh inverse problem from scratch for every new observation, we spend computation once during training and reuse it many times later. This is called _amortized inference_.

In our example in cryo-EM, concretely, this means after training on large batches of synthetic images (from the forward simulation), the model can return a posterior for each newly acquired image without rerunning expensive sampling pipelines from zero.

After a few more core ideas we will come back to the exact implementation of this. But first, ...

### ... why posteriors are better than point estimates

A point estimate answers: "What is one plausible parameter value?" A posterior answers: "Which values are plausible, and with what uncertainty?" For inverse problems that are ambiguous or ill-posed, this distinction is critical.

If multiple parameter settings can explain nearly the same observation, the posterior should represent that ambiguity explicitly. This makes scientific interpretation safer and more honest, especially when downstream decisions depend on uncertainty.

This can be illustrated by our cat example: a cat lying down and a cat standing, both seen from the top, can produce very similar projections, potentially indistinguishable once noise is added. Yet the underlying states are different. More generally (and applicable to proteins), different conformations or orientations may produce similar image evidence. A posterior can represent this multi-modality, while a single estimate can hide it.

We ourselves have trained a few models on cats in different conformations. Below, you may check out the cat we used as well as just experiment on some estimated posteriors! If that feels daunting, no worries; there's a collapsable explainer box beneath the widget which may help to guide you through it.
