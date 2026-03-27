The 2D case motivates how this is directly relevant for Cryo-EM: because our data are images and because many imaging effects are easier to understand in frequency space than in pixel space, using the Fourier language is making things _a lot_ easier.

After a brief contact in the very beginning of the course, we now want to officially introduce you to our test subject: _cat_.

# Detour: What is an _object_ and what do we care about?

Until now, we talked only cryptically of apertures and objects. However, as we are actually measuring _something_, we wanted to choose one "object of study" and guide you through the concepts with that. Although cats are of no particular interest to Cryo-EM and structural biology, we see one huge benefit: you have an _intuition_ about cats, which is one of our main concerns in the project. You are familiar with how it should look, and how it can behave. For example, you can make out details by eye and the "structure" is interesting enough to manipulate, while not loosing yourself in details Essentially, it does not matter what the object is for the fundamentals, but we think its much more fun like this. However, the particular details how we "construct and treat" the cat are quite interesting to study.

We use a 3D-model of a cat (or anything else). To connect it to physics, we then model this cat as a cloud of electron densities around the underlying points making up the 3D structure. This is where in reality we have scattering and interaction coming from, when the electron beam of the microscope hits an object, and we wanted to mention that briefly for completness.

The cat example also allows us to ask for _functionality_. We hope you agree that a cat "getting food" in comparison to "resting", will look different although it is the same cat. We can clearly differeniate a cat standing or lying on the ground, respectively, and in that sense assign a function to both poses.

If you understand this, a _protein_ – the thing that is actually of interest to structural biology – is not really different! We want to image the structure and understand or learn how form follows function.

With that in place, we can now start our first interesting manipulations.

# Manipulations in Fourier space

What you now see on the left is a projection of the cat in real space. If a wave hits this "slice of cat", this will produce a Fourier transformation of it as discussed above. To illustrate, we now take the power spectrum of the Fourier transformed wave (its squared amplitude) and you should manipulate it. Note that every manipulation affects _frequencies_ now, and the origin has frequency 0 (so the magnitude increases outwards in all directions). Observe and try to deduce the "pattern" that certain frequency manipulations have on the reconstruction from the altered spectrum on the right.
