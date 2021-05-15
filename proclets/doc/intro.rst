..  Titling
    ##++::==~~--''``

Introduction
::::::::::::

Petri Nets are a way to describe all sorts of real-world processes.
They have many applications in Physics, Chemistry and Biology.

In Software Engineering too, when we need to design a distributed system, we want to build a model of that system
first, so we can understand how the components must interact.

Since the 1970s software architects have used graphical notations to describe operational behaviour. Most recently
UML has standardised those notations into over a dozen different diagram types, each with its own particular
focus; hence each well fitted for some aspects of design, but less so for others.

While UML is well specified for modeling sequential workflows, it lacks exact semantics around the synchronisation
of concurrent ones. Conversely Petri Nets, though they elegantly portray the behaviour of concurrent processes,
originally lacked some of the logical and relational features required in a systems design notation.

A fusion of the two is described in
`Proclets: A framework for lightweight interacting workflow processes
<https://dblp.org/rec/journals/ijcis/AalstBEW01>`_ (2001) by Van der Aalst, Barthelmess, Ellis and Wainer.
It shows how to constrain Petri Nets so they behave predictably enough to be a model for business workflows, and it
adds a UML-like relational notation to describe where discrete processes synchronise together.

This **proclets** package provides the classes described in that paper.

This means you can sketch out a process in pencil as a Proclet and then implement it in Python code
without leaving that conceptual framework.
Hopefully this makes it a simpler job to verify that your code accurately realises the model.
