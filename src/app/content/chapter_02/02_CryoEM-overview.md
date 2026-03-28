## What do you need in order to _understand_ Cryo-EM?

### Chapter 2 lesson sequence (implemented)

This file remains the original brainstorm and planning draft.

For the learner-facing sequence, use:

1. Waves and Diffraction
2. Fourier Intuition from 1D to 2D
3. Lenses, PSF, and CTF
4. Ewald Sphere and Projection-Slice
5. CTF in Real Cryo-EM Images
6. SPA, Sample Prep, and Heterogeneity

Missing widgets are explicitly marked as TODO-widget in the corresponding lesson files, including expected learning outcomes.

One of the main goals of this project is to have a ressource which distills all the required knowledge needed to understand CryoEM into one page. CryoEM is not easy to understand subject. We will assume that the reader has at least an undergraduate level of training in maths or physics. Even then it still a journey to really _understand_ exactly why and how CryoEM works. We will won't skip out on details necessary to really understand the foundations but we will be brief regarding specifics or advanced material as thats not the focus here.

The following is the minimal (in our view) pipeline to deeply understand the basics and not just accept them:

- Theory of Diffraction (Huygens, Fresnel, Kirchhoff)
- Fourier Transformations
- Lenses Image Formation
- Ewald Construction, Projection-Slice Theorem
- CTF
- Sample Prep and SPA

To understand the particular problem the paper adresses a molecular biology excursion is needed although is but a small detour.

editors note: first idea of what will be text blocks and what widgets

- diffraction explainer
  - its all waves, always has been -> how do waves propagate?
    - > Huygens principle, Fresnel
      - (widget of two point sources spreading and interfering, with one phase adjustable?)
    - > Kirchoff Integral - fraunhofer approx
      - widget of some aperture and you move the screen further and further and boom in very far away its the fourier transformation
    - its not at all obvious that for those approx a fourier transformation pops out, we're much more used to fourier trafos in a different context
      - good way to think about it is as a basis transformation from real-space to frequency space. for 1d signals it a easy to understand frequency basis is sine functions with distinct frequencies, sound being an intuitive example but works for everything
      - (typical fourier widget)
      - for 2D signal which we can display as images, the frequency basis function are plane waves with different directions and frequency (we are in 2D after all)
      - (similiar widget but in 2D)
      - The fourier space of an image thus encodes its spatial frequencies
        - low frequency: general structure, large spatial features
        - high frequency: edges, sharp details
      - (triple view widget: real space image - power spectrum - filtered rs image; donut shaped, adjustable mask in power spectrum with few pre-sets to explore effects on resulting image)
      - theres also some neat math involved, we need to remember:
        - invertability (easy to explain if you think about changing basis)
        - convolutional theorem (idk how to explain that)
    - reminder: its exactly the fourier decompostion which pops out in the fraunhofer approximation
  - hey remember the little adjustable applet showing how changing the phase of one source kind of changes the direction of the constructive interfering beams? thats how lenses work lol! i dont know if we can explain that succintly tho
  - alternative would be: lets take the defining feature of a lense: a plane wave going out becomes a point in the focal plane. now put in the difference between back focal plane and front focal plane and what do we see? 1 everywhere becomes a single point? reminds you of something? that is a fourier decomposition! we are aware that this part of the explaination is hand wavy (nevertheless quite instructive in our view) but we dont want to write a whole book, so we just accept that key take away that lenses perform a fourier decomposition
  - this allows us to formulate a very basic theory of imaging:
    - some exit wavefront starts propagating in the object plane (how that exit waveform is formed is another chapter, well get to that)
    - in its far field, we get the fourier decomposition of the exit wavefront
    - now we place the far field (fourier decomp) in the backfocal plane of a lense and then in the front focal plane of the lense that become the FT of the FT ergo we get the exit wavefront back (maybe use the same two points from earlier) obviously has its limitations such as placing a lense infinetely far away is tough to do, so you might be inclined and and another lense to parallelise the outgoing beam first but we think that added complexcity is just a nuisance and not fundemantelly more helpful.
      important things to take away from here: - this models opens our minds to the fourier plane (e.g. far field of the object / bfp of the lense). This is a space we can access both physically (its a literal plane in any microscope) as well as computationally (take the fourier transform of the image). See how we did not capture the whole fourier space of the exit wavefront? that means we are not gathering some of the higher spatial frequency information in our reconstruction essentially losing it. that defines a classical limit in your resolution.
    - how to measure "image quality" of such a system?
      - well an obvious way to do it is to test whether the imaging system does its job well - a point in the exit wavefront should correspond to a point in the detector. It turns out that it never does its job perfectly well, be either because we're not capturing all the high resolution components or our lenses are not very good or the wave medium is uneven or any number of things. That is visible in the Point-spread function; this is simple the image on the detector formed by a single small point source in the object plane.
      - combine this with the huygens which told us that any wavefront (such as the exit object wavefront) is composed of infinitely many point sources and you can get a valid model of image formation in physical systems. you look at the effect each individual point source of the exit wavefront (which will correspond to a psf on the detector) and say that each and every point source in the exit wavefront has that effect. essentially what you are saying is that you need to convolve the object wavefront with the psf to get the final image formed.
        Image = Conv(Obj,PSF)
      - this is in principle intuitive, but if you just give someone a PSF and an object exit wavefront they'll have a hard time articulation how exactly a convolution of the PSF acts on that. The PSF acts on the object exit wavefront in real space with a convolution. We've learned that we can also describe the whole process using the fourier space, as thats just a change of basis. One might wonder how that looks like...
      - we've learned that the fourier plane is but the fourier transform of the image, so lets just fourier transform our equation above:
        FT(Image) = FT(Conv(Obj,PSF))
        use conv theorem
        FT(Image) = FT(Obj)*FT(PSF)
        the fourier transform the PSF has a special name, its called the Contrast Transfer Function (CTF)
        FT(Image) = FT(Obj)*CTF
        So now instead of thinking about the effects of a physical imaging system as a convolution of the exit wave front with the PSF we can think about it in the fourier space. The FT of our formed image can be described by the FT of our object exit wavefront multiplied by the CTF function. in fact, you've already done this earlier in widget something! You masked off specific parts of the fourier spectrum of the obj exit wavefront and observed the effects that masking had on the final formed image. You essentially modified the contrast transfer function by hand! Isnt it satisfying how everything fits together?
  - Recap: - The far field of a propagating wavefront is essentially the fourier transformation of that wavefront (fraunhofer approx) - lenses perform a fourier transformation between their FFP and BFP - starting with some wavefront exiting an object and placing the BFP of a lense at its far field, yields an image of the object exit wavefront in the FFP of the lense. Since we cannot capture the whole far field (fourier spectrum) of the object exit wavefront and our lenses are imperfect, this yields to imperfections in the image formed. In real space they can be described with the PFS (the image formed by a single point source); the final image is the convolution between the object exit wavefront and the PSF (referring back to Huygen). While a valid view, we'll mostly stick to examining the fourier plane. The image formation process can be desribed in fourier space as the multiplication of the FT of the object exit wavefront and the FT of the PSF, which we'll call the CTF. This CTF essentially serves as a continious mask determining which spatial frequencies of the object exit wavefront are allowed to contribute (and how much) in the final image formed. This interpretation is nice stuff like cutting out high frequencies or damping low frequencies have easily visualisable effects and its computionally much more efficient when simulating imaging (but thats a spoiler)
    Maybe some of this material gave you flashbacks of your optics lectures; why are we not talking about electrons??? Thats because so far all we have assumed is that we have propagating waves and lenses. You might immediately think about typical light microscopes and yes, this framework indeed works for typical light micoscopes. But this theoretical framework works for _any_ propogating wave for which we can build lenses. All this build-up with theory just for the following reveal:
    Essentially^\*, theres nothing special about an electron microscope compared to a light microscope like you used in 3rd grade science class.

this is absolutely rage-bait of course but its also pretty much true. Sure everything gets _much_ more complex when trying to work with electrons instead of photons but there really arent fundamental differences; it's all diffraction theory (insert astronaut meme).

We hope this part was enlightening. It took us lots of time wrapping our heads around it but we believe the above story to be a minimally viable framework to really _understand_ shared aspects of all imaging systems and not just accept them at face value.

But alas, it is time for us to talk about the object exit wavefront. We believe in a clear seperation between _what_ is imaged and _how_ is it imaged. The above story was fully about the the _how_ and now comes the part about _what_. Because we typically want to image _physical things_ and those physical things interact with the propagating waves. Our usual set up is to subject our object to coherent plane waves of our choice, those coherent plane waves then interact with our object in some way shape or form which then forms the object exit wavefront. Ideally the interaction between coherent plane wave incoming and the object lead to some change in the exit wavefront which we then image and interpret. (this part is tough to word honestly but thats how i think about it...)

Lets talk Ewald Sphere. i dont know if my seperation with object exit wavefront is pedagogic or correct, heres how perplexity would continue

- Upgrade from 2D mask to 3D scatterer

So far we secretly treated our specimen as a thin 2D mask: the object just imprints some complex amplitude onto a plane wave, and off we go with our Fourier optics story. Real specimens, of course, are 3D collections of scatterers. A more honest description is a 3D scattering potential  
\( V(x,y,z) \) that the incoming plane wave interacts with.

In that picture, each atom contributes a little scattered spherical wave. Summing all of them and propagating to the far field is equivalent to taking the 3D Fourier transform of \( V(x,y,z) \); there a a certain three dimensionality to the fourier space.

The important point: for a given incident plane wave, not all \( \mathbf{q} \)-vectors are allowed by the geometry and energy conservation of elastic scattering.

### Introduce wavevectors and the sphere

Enter the Ewald sphere. We describe the incident beam by a wavevector \( \mathbf{k}\_0 \) and any scattered beam by \( \mathbf{k} \). The scattering vector is

\[
\mathbf{q} = \mathbf{k} - \mathbf{k}\_0
\]

Because the scattering is elastic,

\[
|\mathbf{k}| = |\mathbf{k}\_0|
\]

which means all allowed \( \mathbf{k} \) lie on a sphere of radius \( |\mathbf{k}\_0| \).

If we pin the tail of \( \mathbf{k}\_0 \) at the origin of reciprocal space, this condition carves out a sphere—the **Ewald sphere**—on which all the accessible \( \mathbf{q} \)-vectors must lie.

Now recall our beloved Fourier plane: the back focal plane of the objective. Each point in that plane corresponds to some scattering direction, i.e. to a particular \( \mathbf{k} \) and hence a particular \( \mathbf{q} \).

The NA of the objective just limits the angular range of \( \mathbf{k} \) we collect, so instead of sampling the whole Ewald sphere, we only get a spherical cap.

Project that cap down onto the detector, and you’re back to exactly the 2D Fourier-space picture we started with—but now you know where it sits in 3D reciprocal space.

grrrr, not satisfactory IMO. Nevertheless, the important part is that the Ewald sphere has a radius of 1/lambda. For Electron Microscopy you will thus observe that locally at the origin it looks almost flat. What we observe on in the far field is thus quite exactly a slice through the fourier transform of the object's electron density.

There is a super clean explaination of the projection-slice theorem which makes sense but rn im tired
(probably have a widget here ig)

And now its all coming together. We have established that in Electron Microscopy, we get projections of the 3d electron density of our imaged objects. But this alone is not enough characterise EM. While this is indeed the geometry of how we image our sample it doesnt tell us much about what the resulting image will look like. As we covered previously all optical systems, perfect and inperfect, cannot _exactly_ capture the sample. We have to consult the contrast-transfer function. This will tell us how the microscopy alters the image. It will not just be a slice in fourier space infinitely large but instead be modulated and cut off by the CTF in fourier space before we re-transform into real space. And if you thought you can get drastic effects with the little donut shaped CTF in the applet earlier, you aint seen nothing.

This can be theoretically derived but I think it speaks for itself: Based on just a few key parameters:

- defocus
- B
- whatever
  this highly oscillation function bounded by the exponential pops out.
  (interactive CTF with cat picture, maybe some presets aswell)
  Remember that the CTF is how you modulate the true fourier slice of your object before you transform back to the image. thus a zero crossing means you lose all information regarding that spatial frequency in your image. As you commenly have zeros at very low spatial frequencies you lose some of the larger structure and get contrast inversion. A special mention also goes to the noise. Since we dont want to bombard our samples with high intensity electron radiation in order to preserve their health (as in not destroy the very structure we aim to find out) EM often works in regimes where only few electrons are captured per image leading a great amount of noise for individial images. Combine the two factors and you get resulting images which are very hard to decipher and make sense of individually.

This opens the door to Single Particle Analysis. This is a quite commong technique in EM and involves purifying many different instances of the same structure (e.g. aa ribosome). It's important for later that we actually really have exactly the same structure. I shall already spoil our end goal: If we were to have access to the full 3d fourier space of an object, we immediately could reconstruct that object itself (with FT just being a change of basis and all). We established that for a single picture with an electron microscope we get one slice in that 3d fourier space. The neat idea is to simultaneously image many instances of the same structure at once. The way we prepared the sample each individual instance will have a random orientation. But if you image many instances with random orientation at some point you will image most orientations many times. Now that you have projection images of your object in all orientations (and since they are each projections you now have slices in your objects 3D fourier space in many angles) you can use some clever maths to reconstruct the 3d shape of the object, which is the ultimate end goal. The important bit here is that any individual image is really rather noisy. In order to get reliable results you would first identify a great many projection images with the same orientation of the particle and then average thus to get a 'reliable' example of a projection of that angle. Averaging many individually noisy images of the same projection leads to a significant increase in signal to noise ratio because true signal adds up while noise averages out.

Now this should just be a brief, yet important, excursion but how to prep such a sample? First you identify a structure of your choice, often a protein you are interested in. A biochemist of your choice is then instructed to purify or create that protein. Now the shape of proteins is heavily dependant on their environments. The water in your cells really does play a crucial role in influencing the folding of proteins and if we want to properly study such proteins we must make sure that they are in their native environment, eg. surrounded by water.

That is actually a problem for EM people. Electrons, in contrast to for example photons, interact very strongly with almost anything. Because _everything_ is made out of atoms with electronic shells so electrons just flying around have plenty of ways to interact with their environment. In order to get the electrons from the source in the EM to their target you must does, metaphorically, clear the road. And that means you work under vaccuum. That means your sample must be able to withstand vaccum which regular water very much does not. Thus the idea was born to very quickly freeze the sample (if you do it quickly enough you arrest most movement very fast thus not giving the water molecules enough time to settle in a crystalline structure; this is important because this would once again alter the shape of the protein). you also arrest the motion of your target protein. (i think we should skip the whole dubuchet freezing stuff cuz it really doesnt add anything but complexity does it?)

Here we make a brief excursion into ATPase which has a great exampleon how function follows form. Bla bla bla, different conformations in a cycle lead to repeated booping ADP+Pi together thus creating ATP. huzzah!

Truth of the matter is that the molecular world is in fact very noisy and not as rigid as one would think. Molecules may find themselves in a great variety of different conformatinos depending on their environment and the context. Much like a cat may sometimes be standing and walking around or sometimes just lie down; yet it always stays a cat. That complicates our simple picture of SPA. We actually want to study a protein in all its conformations to get a better understanding of it; if we would only know a lieing down cat we would not know that it is a great hunter of mice.

expand on: in typcal samples we have a large conformaitonal heterogentiy?

To tie it all together: before you can even begin to group together projections taken from the same orientation you should ideally make sure that the depicted projections stem from objects with the same conformation! But that seems like a hard task given all the CTF shennenigans and noisy images, right?
