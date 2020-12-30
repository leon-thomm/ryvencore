# Welcome to the `ryvencore` documentation!

Looking for a quick start? Visit the [Getting Started](/getting_started/) section.

## Project Idea

!!! tldr
    ryvencore is an easy to use framework for creating flow-based visual scripting editors for python.

ryvencore comes from the Ryven project, a small, flexible flow-based visual scripting environment for python. As requests for Ryven versions optimized towards specific domains increased, I recently started to think about creating a small package that implements the core functionality of Ryven but has an intuitive API for creating similar editors.

And there we are. The API, as it is right now, is much more intuitive than I had imagined, which inspired me to open this project for others and create a documentation page.

!!! info
    Since the biggest part of the code deals with management of the GUI (in particular drawing and interaction of nodes and flows) and a package not implementing this would be almost empty, ryvencore already provides you with those GUI classes, so it's not GUI independent, it depends on PySide. There might be ways to integrate the PySide-based widgets of ryvencore into other GUI frameworks, but it is recommended that you use a Qt-based environment. Setting up a window with PySide or PyQt is quite straight forward.

Besides essential GUI classes, ryvencore also provides you with a few convenience classes which you may want to use, which only use ryvencore's public API, making it much easier to get started.

!!! warning
    ryvencore is not a professional software and sometimes there are major changes. Just be aware.

## Current State

In it's current state ryvencore is very experimental. It works quite well so far and I will definitely use this in the future to create a few more specific visual scripting editors for python. But it is a pre-alpha.

## Resources

May I also direct you to the [website of the Ryven project](https://ryven.org) if you haven't been there already. And there's a [YouTube channel](https://www.youtube.com/channel/UCfpqNAOXv35bj_j_E_OyR_A).