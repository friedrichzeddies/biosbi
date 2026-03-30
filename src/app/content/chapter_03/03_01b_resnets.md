### A practical SBI workflow

In practice, SBI is often organized in two stages. In a simulation stage, we generate many synthetic samples and train the estimator. In an inference stage, we evaluate the trained estimator on real observations and obtain posterior predictions. The simulation stage may be computationally heavy, but it is usually cheaper and more scalable than collecting equivalent real data.

In our use case, microscope time—which often involves multi-million dollar equipment—and sample preparation are incredibly expensive and time-consuming, whereas large-scale simulation can run continuously on remote compute infrastructure. In this project, simulations are relatively cheap because they rely on random sampling and comparatively simple image-generation steps. SBI exploits this asymmetry by shifting effort from costly physical data acquisition to scalable background computation. 

#### Images are of large dimension

Our data are images, not small tuples such as energies or coordinates, so the input dimension is large even at low resolution. This matters for two reasons. First, high-dimensional inputs increase computational cost. Second, not every pixel is equally informative; many pixels contribute little to parameter recovery. To address this, we use **summary networks** $h$ that extract compact and informative features,

$$
s = h(x).
$$

These summaries serve as learned preprocessing for posterior estimation. A common architecture is the ResNet, which can be scaled to different compute and expressivity requirements. We unfortunately don’t have the time to get into the specific neural network architectures used for vision processing, but briefly: Residual Networks (aka ResNets) use skip-connections to help train *deep* convolutional neural networks (the backbone architectural operation for image processing in machine learning). If you know, you know.

To give you a small break from the, admittedly very heavy content we just presented you with, we’ve made a small widget which allows you to see what a summary network actually does. 

Bad news: it’s not going to make a lot of sense to us humans. In order to not crowd the main text, there is a collapsible box underneath the widget that may help to guide you to some interesting observations about the summary network. Note that while we show the output as an image (because it still has a high dimension) one really needs to keep in mind that at the stage of the summary network, it is not meant to be interpreted as an image in the sense a human understands it. The summary network ideally learns meaningful connections between an image and an abstract lower dimension space – so don’t be too sad if it doesn’t make sense. We are only human, after all.

