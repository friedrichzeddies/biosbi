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

As indicated above, SBI methods train neural estimators on simulated data. Depending on the method family, one may learn a posterior, a likelihood surrogate, or a likelihood ratio. A common target is direct posterior estimation $p(\theta | x)$ from the many simulated pairs $(x_{sim}, \theta)$. Remember,the posterior is a probability distribution in parameter space which describes how well a given parameter $\theta$ explains the observation $x$. In Neural Posterior Observation (_NPE_) we learn to directly estimate this posterior:

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

This type of dimensionality reduction is quite abstract. It’s also quite useful not only for reducing compute but also turns out to be a great tool one can use to check whether the learned model is not misbehaving. These summaries serve as learned preprocessing for posterior estimation. A common architecture is ResNet, which can be scaled to different compute and expressivity requirements. We unfortunately don’t have the time to get into neural network architectures used for vision processing; but briefly: Residual Networks (aka ResNets) use skip-connections to help train _deep_ convolutional neural networks (the backbone operation for image processing in machine learning). Don’t worry if that’s just gibberish to you.

To give you a small break from the, honestly very heavy content we just served, we’ve made a small widget which allows you to see what a summary network actually does. Bad news: it’s not going to make a lot of sense to us humans. In order to not crowd the main text, there is a collapsible box underneath the widget that may help to guide you to some interesting observations about the summary network. Note that while we show the output as an image (because it still has a high dimension) one really needs to keep in mind that at the stage of the summary network, it is not meant to be interpreted as an image in the sense a human understands it. The summary network ideally learns meaningful connections between an image (as a human would understand) and an abstract lower dimension space – so don’t be too sad if it doesn’t make sense. We are only human, after all.



[widget]
[collapsable box text:
Interesting observations:
Recommend the 10 cat model: 
use view from the side -> summary changes a lot
Use view where confirmation looks a like (-30,0,-90) -> doesnt change that much
]


