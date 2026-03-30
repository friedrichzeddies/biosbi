### Fraunhofer Approximation and Fourier Intuition

As you might have noticed, close to the aperture, the pattern is still localized and busy. Farther away, a surprisingly clear structure emerges. The functional form of this theoretically expected result is the well-known $\text{sinc}(x) = \frac{\sin(x)}{x}$. Importantly, as you move far away, the diffraction pattern seems to converge to this function. Why would the diffraction pattern formed far away be so well behaved?

That's something that many great thinkers have pondered over the centuries. The answer can be derived by using the Huygen-Fresnel principle and setting up your equations in a clever way. Skipping over a lot of history, Kirchoff formulated the problem in the following manner:
![Graphic: Geometic construction of the Kirchhoff integral.](../../assets/EBP-01-KF_Diff.png)

Solving how waves diffract involved the Kirchhoff integral, which describes how the field value of a wave propagates after passing the aperture.

$$
E(x_0, y_0) \propto \iint
\exp\!\left[
i k \left(
\frac{x_1^2 - 2 x_0 x_1}{2 z}
+
\frac{y_1^2 - 2 y_0 y_1}{2 z}
\right)
\right]
\, \text{Aperture}(x_1, y_1)\, E(x_1, y_1)\, dx_1\, dy_1
$$

Because this integral is quite difficult to solve analytically, we apply the *Fraunhofer* (or *far-field*) approximation. The terms simplify significantly, giving us:

$$
\begin{align}
E(x_0, y_0) \propto & \iint
\exp\!\left[
i k \left(
\frac{- 2 y_0 y_1 - 2 x_0 x_1}{2 z}
+
\underbrace{{\frac{x_1^2 + y_1^2 }{2 z}}}_\text{negligible}
\right)
\right]
\, \text{Aperture}(x_1, y_1)\, E(x_1, y_1)\, dx_1\, dy_1\\
&\boxed{\propto \iint  \exp\!\left[  - \frac{i k}{z} \left(
y_0 y_1 + x_0 x_1\right)\right]
\, \text{Aperture}(x_1, y_1)\, E(x_1, y_1)\, dx_1\, dy_1}
\end{align}
$$

The far-field approximation can be boiled down to the scenario where the observational distance is very large compared to the wavelenght. Since (particle) wavelenghts are quite small compared to the macroscopic world, this is often the case. 
For all alert readers this screams the first fundamental result of our course: **Diffraction of light at an aperture produces a Fourier transformation of the aperture when catching it in the far field**. And interestingly, this applies for any kind of aperture or object! Even more interestingly, this is a general behaviour of waves. The derivation is no different for water waves, electromagnetic waves or particle waves. Electron Microscopy suddenly doesn't seem that unreasonable, does it?



### Fourier Intuition

With this first pillar established, let's take a well-deserved, intuitive look at the Fourier transform without relying solely on formulas. We aim to move from merely accepting Fourier transforms to mentally easily switching between real-space and frequency-space language without feeling like you changed subjects.

The cleanest way to get there is to begin in 1D, where frequency components are the familiar sine and cosine building blocks, and then carry that exact logic into 2D, where the basis functions become plane waves with distinct directions and spatial frequencies. Nothing fundamentally new is introduced in that jump, but your visual intuition has to catch up; that is precisely what this section is for. You have probably seen similiar visualisations on Youtube before, but did you ever get the change to play around with it yourself?

It should help you treat the Fourier transform less like a mysterious operation and more like a coordinate change. You are describing the exact same object in a new basis where some physical questions become vastly easier to answer.

In the interactive sequence below, start by turning individual 1D components on and off, then alter amplitudes and phases until the reconstruction behavior feels intuitive rather than surprising. After that, move into the 2D decomposition view and watch the exact same logic reappear with directional components. A question to check your understanding: if you can explain how the superposition of frequencies produces the original signal, can you also explain why some specific frequency components are exactly zero? How would the structure of the image change if that specific frequency is _not_ equal to zero?
