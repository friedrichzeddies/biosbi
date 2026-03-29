## Chapter 1 - Introduction

Welcome to our Generative Neural Network for the sciences final project. Buckle up, get yourself your favourite drink, and make learning feel like a fun blessing for your free time!

### Why we do this (except for some credit points)

The harsh truth up front: cryo-Electron Microscopy (cryo-EM) and Simulation-Based Inference (SBI), using GNNs under the hood, are terrifically hard nuts to crack conceptually. But - unfortunately or luckily, depending on the day - they are also the two subjects we, Sebi and Friedel, are most interested in during our Master's degree. Hence, when we were tasked with finding a topic for our final project, we wanted to do something we are passionate about. And since we, as students who took some courses in these fields (not quite experts yet), also find it hard, we can imagine others might feel similarly.

We also strongly believe that learning happens by _using_ and messing around with stuff, rather than by only attending a lecture or watching a video. We also acknowledge that a scientific paper is absolutely the right format for its purpose; experts work incredibly hard to inform other experts who already know a lot, in an incredibly concise way. But the truth is: getting through that can take a lot of time, and the process of understanding and learning is often neither fun nor very pedagogical.

Enter **biosbi**: a website playground collecting the pure essentials and fundamentals of biophysics and SBI / GNNs, and intertwining them with each other. We aim for a broad and thorough explanation of both topics that is content-wise enriching, but at the same time does not make users fall asleep or terrify them with math.

In order to achieve this, we want to make this project as interactive as possible, because many things that sound complicated and frustrated us while learning actually have the potential to be visually pleasing and manipulable, so one not only learns _what_ it is, but _how_ it behaves and feels to work with.

We think there are only very few people around who fully grasp both subjects, and quite possibly also not a lot who understand them even _partially_. This is true both for scientists who never got super deeply in touch with the other field and for students who are still trying to figure out their path and have not had enough time yet to see all the possibilities. Let's briefly motivate why each group might want to play around a little with our site.

#### For our fellow students

Lecture, exercise sheet, tutorial. Lecture, exercise, tutorial. On a good week, you can squeeze in a YouTube video you think is great but do not really listen to, just to escape this hellish cycle, these grey weeks of boring education. But behold, here comes the sun! 🌞
What if we offered you a way to explore a field you never heard of, or are just getting started with, maybe even two at the same time? What if the process was not "struggling to grasp a topic," hearing a lot of extra stuff on top, and then forgetting the basics again before actually working with it? Visuals instead of formulas and text, dynamics instead of statics, understanding over merely hearing about it. We missed that many times in our previous studies. In these two fields, there are plenty of opportunities to connect ideas and play around, which makes it a great chance to become curious again, like when we started.

#### For our Biophysicists who never heard of SBI

Do you like staying up until 2AM to "take just a few more images" with your electron microscope? Or going to the lab over and over again to freeze your samples? Or staring into the wallet that is missing about 3 million euros and hoping it materializes out of thin air any moment now? Do you _really_ like it? Well, even if you do, because 2/3 of those things can be awesome at times, you probably cannot deny that it takes a lot of resources: time, people power, resilience, and money.
And in the end, the images are only half the truth. Extracting useful information from them is a pretty hard task people have been searching answers to since... forever.
In case you never heard about SBI, the third chapter gives insight into how this framework, combined with good computational resource allocation and modern architectures, helps solve this kind of problem in general, resulting in a few very good reasons to consider it.

#### For our Computational Ladies and Gents looking for use cases

Pure math and a lot of coding - the world of generative AI is not always very applied when researching the next powerful, yet abstract algorithm, architecture, or framework. And you might sit there at your desk with a cup of coffee, the GPU catching smoke just thinking about training your newest architecture improvement, and ask yourself:
_"What is this for? I haven't seen an immediate use of this for a little while now..."_
While the broader concept of SBI is pretty straightforward, the exact details are not always easy to wrap your head around. For us, the concept only _really_ clicked when we analyzed a practical use of the framework with the SRI model on a specific task. And while many good illustrations exist, we think this one is special because it sits a bit outside the usual comfort zone. For some, it might open up a new horizon of applications and inspire out-of-the-box thinking - or help confirm that coffee and GPU smoke are the perfect Tuesday for the rest of your life.

#### A brief manual

This website is built to be intuitive, but for completeness we briefly explain _how to use this thing_.
Essentially, we serve a super fancy Jupyter notebook, running Python code packed into a very nice casing via `streamlit`. In a nutshell, you can do nothing wrong. We coded and implemented interactive blocks, and you explore them. By using fields and submitting input, you can and _should_ manipulate as much as possible and inspect the results, connecting them with what you read before. In the backend, we implemented boundaries so the code does not do anything extremely wrong, so technically you should not be able to break anything - and if you do, please send us an email with a picture ridiculing us or contribute to the project on GitHub.

In summary, the world (or rather this site) is your binary oyster program.

#### A starting challenge

In order to finally get started, put some ✨intuition✨ behind the rather unspecific words we used so far and, in line with our goal to keep things fun and interactive, take a moment to ponder this question:

[Interaction: What is the explanatory variable for this blob slice? or something similar, Quiz like with a few answers and funny responses or so?]
