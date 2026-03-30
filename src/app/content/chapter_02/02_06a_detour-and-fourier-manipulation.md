### Detour: What is an _object_ and what do we care about?

Until now, we have talked only cryptically of apertures and objects. However, since we are actually measuring _something_, we wanted to choose a concrete "object of study" to guide you through these concepts. Although cats are of no particular interest to cryo-EM and structural biology, we see one huge benefit: you already have an _intuition_ about cats, which is one of our main priorities in this project. You are familiar with how a cat should look and how it can behave. For example, you can make out details by eye, and the "structure" is interesting enough to manipulate without losing yourself in the details. Essentially, the exact object doesn't matter for the fundamental physics, but we think using a cat is much more fun. Moreover, the particular details of how we “construct and treat” the cat are quite insightful to study.

To connect it to physical electron microscopy, we then model this cat as a cloud of electron densities built around the underlying points making up the 3D structure. In reality, this is where the scattering and interaction originate when the electron beam of the microscope hits an object. We wanted to mention that briefly for completeness.

**For a brief moment now, we will only be interested in the cat as a 2D object.** At first, this might sound confusing given the explanation above, but it makes life easier for a few minutes. From the 3D model, we take just a single "picture" (rather, a 2D projection) and manipulate it. This action will be justified when we look at the optional sub-chapter covering the _Ewald sphere_ and the _Projection-Slice Theorem_.

The cat example also allows us to ask for _functionality_. We hope you agree that a cat "getting food" compared to a cat "resting" will look physically different, although it is the exact same cat. We can clearly differentiate a cat standing from a cat lying on the ground, and in that sense, we can assign a biological "function" to both poses.

If you understand this, a _protein_—the thing that is actually of interest to structural biology—is not fundamentally different! We want to image the structure and understand or learn how that spatial form translates into biological function.

With that in place, we can now start our first interesting manipulations.

### Manipulations in Fourier space

What you now see on the left is a projection of the cat in real space. If a wave hits this "slice of cat," it will produce a Fourier transformation of the image, as discussed above. To illustrate this, we take the power spectrum of the Fourier-transformed wave (its squared amplitude) and allow you to manipulate it directly. Note that every manipulation now strictly affects _frequencies_. The origin of the spectrum represents a frequency of 0, so the magnitude of the frequency increases as you move outwards in all directions. Observe closely and try to deduce the "pattern" that certain frequency manipulations have on the reconstructed image on the right.
