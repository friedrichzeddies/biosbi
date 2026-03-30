### Fourier Manipulation: Effects and Intuition

As you can see, directly manipulating Fourier components (spatial frequencies) can produce *strange and unintuitive* effects in real space...

Essentially, the reason for that is another fundamental result of our course: **low spatial frequencies mostly carry global shape, while higher spatial frequencies encode fine details, edges, and the subtle structures that reconstruction quality depends upon.**

You can convince yourself of this by recalling the inverse relationship between real space and Fourier space, $k=\frac{1}{\lambda}$. Once you grasp this, masking and modulation in Fourier space should stop feeling arbitrary and start making intuitive sense. We encourage you to go back, test this explanation, and consciously connect it to your manual manipulations.

If a frequency band is attenuated, zeroed, or inverted, there is a direct and predictable consequence in the real-space appearance. Developing this exact habit of thought is crucial before we proceed to the next chapters.

You now possess the conceptual tool we will persistently reuse: Fourier space is not a mere side note, but rather the most practical language for imaging physics. Next, we connect this representation to lenses, point-spread functions, and the CTF model so that the math and the microscope start speaking the same language.
