## Chapter 1 - Introduction

Welcome to our Generative Neural Network for the sciences final project. Buckle up, get yourself your favourite drink, and make learning feel like a fun blessing for your free time!

### Why we do this (except for some credit points)

The harsh truth up front: cryo-electron microscopy (cryo-EM) and simulation-based inference (SBI)—using neural networks under the hood—are conceptually challenging topics. Fortunately, they are also the subjects we, Sebi and Friedel, really liked over the course of our Master's studies. When tasked with finding a final project involving generative neural networks, we naturally gravitated toward those two topics. Since we found these concepts difficult when we first learned them, we imagine others might feel similarly.

We also strongly believe that learning happens by _using_ and messing around with stuff, rather than by only attending a lecture or watching a video. We also acknowledge that a scientific paper is absolutely the right format for its purpose; experts work incredibly hard to inform other experts who already know a lot, in an incredibly concise way. But the truth is: getting through that can take a lot of time, and the process of understanding and learning is often neither fun nor very pedagogical.

Enter **biosbi**: an interactive playground collecting the fundamentals of biophysics and SBI, intertwining them seamlessly. We aim to provide a broad, enriching and sometimes even fun explanation of both topics without putting users to sleep or terrifying them with math.

In order to achieve this, we want to make this project as interactive as possible, because many things that sound complicated and frustrated us while learning actually have the potential to be visually pleasing. One should not only learn _what_ it is, but _how_ it behaves and feels to work with.

We suspect there are very few people who fully grasp both subjects, and quite possibly, not a lot who understand them even *partially*. This is true both for scientists who never got super deeply in touch with the other field and for students who are still trying to figure out their path and have not had enough time yet to see all the possibilities. Let's briefly motivate why each group might want to play around a little with our site.

#### For our fellow students

Lecture, exercise sheet, tutorial. Lecture, exercise, tutorial. On a good week, you can squeeze in a YouTube video you think is great but do not really listen to, just to escape this hellish cycle, these grey weeks of boring education. But behold, here comes the sun 🌞! 
What if there was a way to explore a field you never heard of, or are just getting started with, maybe even two at the same time? What if the process was not "struggling to grasp a topic," hearing a lot of extra stuff on top, and then forgetting the basics again before actually working with it? Visuals instead of formulas and text, dynamics instead of statics, understanding over merely hearing about it. We missed that many times in our previous studies. Here, there are plenty of opportunities to connect ideas and play around, which makes it a great chance to become curious again, like when we started.

#### For our Biophysicists who never heard of SBI

Do you like staying up until 2AM to "take just a few more images" with your electron microscope? Or going to the lab over and over again to freeze your samples? Or staring into the wallet that is missing many million of euros and hoping they re-materialize out of thin air any moment now? Do you _really_ like it? Well, even if you do, because 2/3 of those things can be awesome at times, you probably cannot deny that it takes a lot of resources: time, people power, resilience, and money.
And in the end, the images are only half the truth. Extracting useful information from them is a pretty hard task people have been searching answers to since... forever.
In case you never heard about SBI, the third chapter gives insight into how this framework, combined with good computational resource allocation and modern architectures, may help alleviate some of your struggles. We think there are a few very good reasons for you to learn about SBI.

#### For our Computational Folk looking for real use cases

Pure math and a lot of coding - the world of generative AI is not always very applied when researching the next powerful, yet abstract algorithm, architecture, or framework. And you might sit there at your desk with a cup of coffee, the GPU catching smoke just thinking about training your newest architecture improvement, and ask yourself:
_"What is this for? I haven't seen an immediate use of this for a little while now..."_
You might enjoy a brief excursion in an unrelated field. Be either either as an inspiration for your next project or just to satisfy your intrinsic curiosity. Do you know how electrons can make images? More importantly, do you want to know?

While the broader concept of SBI is pretty straightforward, the exact details are not always easy to wrap your head around. For us, the concept only _really_ clicked when we analyzed a practical use of the framework with the SRI model on a specific task. And while many good illustrations exist, we think this one is special because it sits a bit outside the usual comfort zone. Electron Microscopy is probably not on the Top 10 list of "things you can easily simulate" for most people (we suspect that's due to most people not knowing a lot about EM). Thus it is even more satisfying to see how well suited Electron Microscopy is for SBI, particularly for a pedagocical endeavour such as ours (humans are inherently visual creatures, after all). For some, it might open up a new horizon of applications and inspire out-of-the-box thinking - or help confirm that coffee and GPU smoke are the perfect Tuesday for the rest of your life.

#### A brief manual

This website is built to be intuitive, but for completeness we briefly explain _how to use this thing_.
Essentially, we serve a super fancy Jupyter notebook, running Python code packed into a very nice casing via `streamlit`. In a nutshell, you can do nothing wrong. We coded and implemented interactive blocks, and you explore them. By using fields and submitting input, you can and _should_ manipulate as much as possible and inspect the results, connecting them with what you read before. In the backend, we implemented boundaries so the code does not do anything extremely wrong, so technically you should not be able to break anything - and if you do, please send us an email with a picture ridiculing us or contribute to the project on GitHub.

In summary, the world (or rather this site) is your binary oyster program.

#### A starting challenge

In order to finally get started, put some ✨intuition✨ behind the rather unspecific words we used so far and, in line with our goal to keep things fun and interactive, take a moment to ponder this question:
