# Features

This site gives a little more detailed overview over ryvencore's specific features. I will introduce the major systems here.

## Nodes System

In ryvencore, nodes consist of a `Node` *object* and a `NodeInstance` *subclass*. This enables highly sophisticated NodeInstances and convenient nodes management software like Ryve's NodeManager. You can put any code into a NodeInstance, no limitations.

Two rules are important when programming NodeInstances:

- When writing an actual application, you need to give your NodeInstance their own source. They can lie all in the same file or in different files, but you should distinct them from other source code.

- Furthermore, if you use custom GUI classes for your NodeInstances (a main widget or custom input widgets), make a clear distinction between functionality that is GUI related and functionaliy that regards the NodeInstance itself. Put everything GUI related into the GUI classes, and everything else into the NodeInstance class.

!!! note
    These two rules allow automatic module-based analysis mechanisms by ryvencore for code generation etc.

!!! note
    Other than a professional implementation might do it, in ryvencore your NodeInstance does not run in a separete thread yet, it's the same as the GUI so far. This of course has significant performance effects, but, for now, I decided to keep the simple system. Separating it would either make ryvencore's implementation *much* more complicated, or restrict your freedom for programming NodeInstances. If I find a nice way to internally implement it, **I might change that in the future.**

### NodeInstance Special Actions

....

## Code Generation (coming soon)

Although this is *quite* experimental and might crash in some cases, if the implementations of your NodeInstances follow the rules above, there's a built in code generation mechanism. Code is generated for a script and contains an abstract version of the flow and the script variables in a structure that keeps an API similar to ryvencore itself, such that all NodeInstances should still work.

!!! note
    **Files might get large!** Because the resulting code has to include this abstract version of the whole internal structure as well as the definitions of used NodeInstances, the resulting code might quickly reach 1000 lines. However, it is quite a strong feature considering you have maximum freedom for programming your NodeInstances.

The resulting code is completely independent, does not have PySide dependencies anymore and can be embedded wherever you need it. There is a function in the code that you can call which creates everything and you will get a list for the NodeInstances and script variables, so you can extract (and even manipulate) the data that you are looking for.

When generating the code, ryvencore runs a dependency analysis of all NodeInstances' sources. Some NodeInstances might just use standard packages and modules (like numpy), while others might include external sources that you want to have included in the generated code, like some functions or classes used by many of your nodes which you therefore keep in their own module/s. ryvencore analyzes normal import statements (not runtime based ones in the code!) and asks you which dependencies' sources should be included. This enables decentralization of your NodeInstance classes (like in Ryven where all NodeInstances have their own file).

## Load&Save

The whole load and save process of projects is done by ryvencore, see `Session.serialize()`, `Session.load()`. Before loading a project, you need to register all required nodes in the session.

## Script Variables

Script variables are a nice way to improve the interface to your data. There is a ridiculously simple but extremely powerful *registration system* that lets you register methods as *receivers* for a variable with a given name. Then, every time the variable's value gets updated, all registered receiver methods are called. The registration process is part of the API of the `NodeInstance` class, so you can easily create highly responsive nodes.

!!! example
    I made a small *Matrix* node in Ryven where you can just type a few numbers into a small textedit (which is the *main-widget* of the node) and it creates a numpy array out of them. You can also type in the name of a script variable somewhere (instead of a number) which makes the matrix node register as a receiver, so it updates and regenerates the array every time the value of a script variable with that name updated.

## Logging

There is a `Logger` class which every script has an attribute of. You can use the logger's [API](../api/#class-logger) to write messages to default logs and to request individual logs and write directly to them. `NodeInstance` already includes methods for requesting individual logs and manages *enable*-and *disalbe*-events according to actions in the flow (like removing NodeInstances), but you can also request logs for anything else.

## Convenience Classes

ryvecore already comes with a few convenience classes for widgets. Those convenience classes only use ryvencore's public API, so if you have experience with Qt, you can totally implemenent them yourself. But in most cases they make it much easier to get started. See [convenience GUI section](../conv_gui).

## Styling

Of course, design splays a huge role when thinking about *visual* programming. Therefore you have  much freedom in styling your flows.

### Flow Themes

There is a list of available flow themes (which I want to expand as far as possible). You can choose one via `Session.design.set_flow_theme()`. Currently available flow themes are *dark tron*, *dark std*, *ghostly*, *blender*, *easy*, *peasy*, and *ueli*.

### StyleSheets

You can set the stylesheet of the session, which will then be directly accessible by all the custom widgets, via `Session.set_stylesheet()`. I am also working on a feature for conveniently styling of the builtin widgets, such as the node selection dialog widgets of the flow.

## Flow Features

ryvencore's `Flow` class, which is a subclass of `QGraphicsView`, supports some special features such as

- stylus events for adding simple handwritten notes
- rendered images of the flow
- touch events (needs improvement)
- algorithm modes
<!-- - viewport update modes -->

### Algorithm Mode

Most flow-based visual scripting editors either support data flows or exec flows. In ryvencore I wanted to enable both, so there are two modes for that. A structure like the flow-based paradigm has most potential for pure data flows, I guess. But exec flows can be really useful too, as can be seen in UnrealEngine's blueprint editor for example.

The technical differences only regard connections. In a data flow, you only have data connections, in an exec flow you can have both. In data flows any change of data (which is setting the value of a *data-output-port* of a NodeInstance) is *forward propagated* and leads to update events in all connected node instances. In an exec flow, contrary to exec connections (which just trigger NodeInstances to update, see `input_called` in `NodeInstance.update_event()`), data is not forward propagated, but requested, *backwards*. Meaning that the API call `NodeInstance.input(i)` calls the connected *output* and requests the data which causes *passive NodeInstances* (those without exec ports) to update/recompute completely.  That's the technical version... Usually, one just wants data flows.

<!-- ### Viewport Update Mode

There are two *viewport update modes*, `'sync'` and `'async'`. The only difference is that in `sync` mode, any update event that propagates through the flow is finished before the viewport is updated. `async` mode can sometimes be useful for larget data flows, in `async` mode, the flow first updates the scene rectangle of the *main-widgets* of NodeInstances before passing the update event to the next connected NodeInstance (so you can see your flow procedurally execute). -->


## Customizing Connections

WIP...