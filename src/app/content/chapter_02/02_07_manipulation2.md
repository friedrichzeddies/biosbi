### Fourier Manipulation: Effects and Intuition

As you can see, the manipulation of fourier components / frequencies does _strange and unintuitive_ things...

Essentially, the reason for that is another fundamental result of our course: **low spatial frequencies mostly carry global shape while higher spatial frequencies encode fine details, edges, and subtle structure that reconstruction quality depends on.**

You can convince yourself of that, if you write out the inverse relation of real and Fourier space, $k=\frac{1}{\lambda}$. Once you know that, masking and modulation in Fourier space should stop feeling arbitrary and start feeling operational and make sense to you. Go back and really convince yourself of the explanation above and try to connect it to your manipulations.

If a frequency band is attenuated, zeroed, or inverted, there is a direct and predictable consequence in real-space appearance, and this is exactly the habit of thought we need before we talk about the next chapters.

You now have the conceptual tool we will keep reusing: Fourier space is not a side note but the most practical language for imaging physics. Next we connect this representation to lenses, point-spread functions, and the CTF model so that the math and the microscope start speaking the same language.
