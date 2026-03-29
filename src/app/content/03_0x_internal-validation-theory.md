Core idea behind SBC:

## The true parameter $\theta^*$ should 'look' like any other sample drawn from the simulated posterior

Alright lets unpack this as this was something we struggled with even tho it's not that deep if you think about it.

One thing to keep in mind is that it is unreasonable to assume our model will be 'perfect'. And as it will never the perfect it's better to know exactly how wrong you are or in other words, how much uncertainty does the inferred parameter value have. This is the beauty of getting a full posterior estimate for any given inference task, such as in amortized neural posterior estimation. You automatically get the uncertainties associated with the inferred paramater for the given input. Our model should be able to 'admit' if it is not sure about what the inferred parameters should be. This can either be due to using too little training data and the model not having reached its full potential but as we've seen there's often also intrinsic 'ill-posedness' in the problem (e.g. top-down and bottom-up projections look the same). With that in mind revisit the earlier statement:

### The true parameter $\theta^*$ should 'look' like any other sample drawn from the simulated posterior

Under the mindset we just established, let's imagine our true parameter theta* to simply be normal distributed for a given input. This is the true posterior p*(theta). And our aim is to train a neural network which acts as estimator trying to get as close to p\* as possible, e.g. make it a normal distribution with the same parameters. But what if we just have samples from the true posterior avaiblabe, as is the case most of the time? How to make sure that our simulated posterior closely resembles the true posterior? Now the elegance of the above idea should become appearant: If a sample of the true posterior looks exactly like a sample from the simulated posterior, we've done a good job of estimating the true posterior.

Now, how to quantify "the true parameter theta* (which is actually just a sample of the true posterior) looks like random samples from the simulated posterior"? Well, the easiest method is to simply compare. Or in fancy words, 'determining the rank of our true parameter theta*". This boils down to very often sampling the simulated posterior and then asking the question "how many of the random samples from the simulated posterior are smaller than the true parameter theta\*".

If we repeat this experiment many times, what would we like to happen? Following our mantra from earlier

### The true parameter $\theta^*$ should 'look' like any other sample drawn from the simulated posterior

then that also extends to the rank of the true parameter theta\*. Over many experiments it should behave just as any other sample from the simulated posterior. And a regular sample from the simulated posterior should sometimes land on the left side of the normal distr, sometimes right in the middle and sometimes on the outside (as compared to other simply sampled points from the posterior distribution as they have the same underlying probability density.). Thus we also would like to see that over the course of many such sampling and comparing experiments, the rank of our true parameter is evenly distributed.

The easiest way to do this is just plot a histogram of the distribution of ranks over many experiments. You can
