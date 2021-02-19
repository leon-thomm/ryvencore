# Getting Started

## Installation

`pip install ryvencore`

Python 3.8+ recommended

## First Editor

!!! info
    You can copy the full example code at the bottom of this page.
   
Let's build our first editor. First thing is importing ryvencore

``` python
import ryvencore as rc
```

### Overall Structure

Your main interface to the current project is the **Session**, which you usually want to create one instance of per application (but you can create more). The constructor already gives options for configurations, but we can leave everything as default for now.

``` python
my_session = rc.Session()
```

Now we want to create a flow, which is part of a **Script**, besides the **script variables** and the **logs**. The scripts are managed by the session, so we just call

``` python
script = my_session.create_script('hello world', flow_view_size=[800, 500])
```

With the `flow_view_size` you can set the pixel size of the flow view that will be created and which you can access via `script.flow_view`. The flow itself is a `QGraphicsView` subclass, which is a GUI class of Qt, so you can directly embed it into your window.

### Setting Up a Window

This is not a complete tutorial on getting started with Qt for Python, but setting up a basic GUI structure is quite simple.

``` python
import ryvencore as rc
import sys
from PySide2.QtWidgets import QMainWindow, QApplication

if __name__ == "__main__":

    # create a QApplication and a MainWindow
    # we'll subclass QMainWindow later
    app = QApplication()
    mw = QMainWindow()

    # creating the session
    session = rc.Session()
    
    # creating a script
    script = session.create_script('hello world', flow_view_size=[800, 500])

    # and setting the flow view as the window's central widget
    mw.setCentralWidget(script.flow_view)
    
    mw.show()
    sys.exit(app.exec_())
```

And there we go, that's it. You can left click into the scene to see a node selection widget pop up. Well, there isn't any content yet to use, so let's add that.

### Nodes

In ryvencore the nodes system works like this:

A node's blueprint is defined by its class, making heavy use of Pythons static attributes system. As the accessible nodes are managed by the session, you need to register the *classes* of the nodes you want to use like this:

``` python
session.register_nodes( list_of_nodes )
```

!!! important "Notice"
    You can put any code into your Node subclass, no limits! You can define additional classes, use external packages, basically everything you can do in a python class.

!!! hint
    You can register (and unregister) nodes at any time! This enables dynamic import mechanisms as implemented in Ryven for example.

Now let's define a simple node. For a detailed description of the members, take a look into the [API reference](../api/#class-node). We'll just create a very simple print node, which prints data provided at an input every time the node is activated.

``` python
class PrintNode(rc.Node):

    # all basic properties
    title = 'Print'
    description = 'prints your data'
    # there is also description_html
    init_inputs = [
        rc.NodeInput('data')
    ]
    init_outputs = []
    color = '#A9D5EF'
    # see API doc for a full list of all properties

    # we could also skip the constructor here
    def __init__(self, params):
        super().__init__(params)

    def update_event(self, input_called=-1):
        data = self.input(0)  # get data from the first input
        print(data)
```

Make your class derive from `rc.Node` and then enhance it the way you like. The `update_event` is the important part, it gets triggered every time the node is supposed to update.

!!! note
    While most flow-based visual scripting software out there implements either the approach of *execution-flows* or *data-flows*, ryvencore implements them both. That's what the `input_called`-parameter is for, you use it when creating active nodes for execution-flows. Generally, data flows are more flexible and powerful, but there are cases where exec flows make more sense, so I wanted to leave it as an option.

And let's add another node which generates a random number in a given range, so we have something to print.

``` python
from random import random

class RandNode(rc.Node):
    
    title='Rand'
    description='generates random float'
    init_inputs=[
        rc.NodeInput('data', widget='std line edit', widget_pos='besides')
    ]
    init_outputs=[
        rc.NodeOutput('data')
    ]
    color='#fcba03'

    def update_event(self, input_called=-1):
        # random num between 0 and value at input
        val = random()*self.input(0)

        # setting the value of the first output
        self.set_output_val(0, val)
```

Note the `widget`-and `widget_pos`-parameters in the NodePort which I explain in the following section.

#### Input Widgets

Data inputs can have widgets, more specifically a *QWidget* (which is a GUI class of Qt) or a subclass. Custom input widget classes can be registered for a node by listing them in the Node's static field `input_widget_classes` (see [API](../api/#class-node)). However, ryvencore also provides you with a few builtin convenience classes (the list will grow in the future). For example the following code creates an input with an input field of the builtin type *std line edit*.

``` python
    init_inputs = [
        rc.NodeInput('data', widget='std line edit', widget_pos='besides')
    ]
```

### Finishing

Now you can run this and if everything works you already have a small editor with all major features. You can place the two nodes, connect them by mouse, type something into the random node's input field and hit enter to trigger the update. It will then update and the `self.set_output_val(...)` call will trigger the connected print node to update and print.

Of course there is much more you can do. For example you can change the flow theme.

``` python
session = rc.Session(flow_theme_name='Samuel 1l')
```

Currently available flow themes are `Samuel 1d`, `Samuel 1l`, `Samuel 2d`, `Samuel 2l`, `Ueli`, `Blender`, `Simple`, `Toy` and `Tron`. And if that's not enough, you can configure the theme colors for those using a json config file, so you'll definitely be able to give your flows a look that fits in the application environment it's going to be a part of. 

You can also change the performance mode to *fast* which results in some changes in rendering.

``` python
session = rc.Session(
    flow_theme_name='Ueli', 
    performance_mode='fast',
)
```

[//]: # ([Star this project on GitHub](https://github.com/leon-thomm/ryvencore){: .md-button })

??? note "CODE"
    ``` python
    import ryvencore as rc
    import sys
    from PySide2.QtWidgets import QMainWindow, QApplication
    from random import random
    
    
    class PrintNode(rc.Node):
    
        # all basic properties
        title = 'Print'
        description = 'prints your data'
        # there is also description_html
        init_inputs = [
            rc.NodeInput('data')
        ]
        init_outputs = []
        color = '#A9D5EF'
        # see API doc for a full list of all properties
    
        # we could also skip the constructor here
        def __init__(self, params):
            super().__init__(params)
    
        def update_event(self, input_called=-1):
            data = self.input(0)  # get data from the first input
            print(data)
    
    
    class RandNode(rc.Node):
        
        title='Rand'
        description='generates random float'
        init_inputs=[
            rc.NodeInput('data', widget='std line edit', widget_pos='besides')
        ]
        init_outputs=[
            rc.NodeOutput('data')
        ]
        color='#fcba03'
    
        def update_event(self, input_called=-1):
            # random num between 0 and value at input
            val = random()*self.input(0)
    
            # setting the value of the first output
            self.set_output_val(0, val)
    
    
    if __name__ == "__main__":
    
        # create a QApplication and a MainWindow
        # the QMainWindow will be subclassed later
        app = QApplication()
        mw = QMainWindow()
    
        # creating the session
        session = rc.Session(flow_theme_name='Samuel 1l')
    
        # registering one node
        session.register_nodes([PrintNode, RandNode])
    
        # creating a script
        script = session.create_script('hello world', flow_view_size=[800, 500])
    
        # and setting the flow widget as the windows central widget
        mw.setCentralWidget(script.flow_view)
    
        mw.show()
        sys.exit(app.exec_())
    ```
   

## Second Editor

**[coming soon]** Here I will just throw at you the commented code for another editor that demonstrates how larger ryvencore editors will generally be structured. It was a first prototype I made for a software to simulate flows of logic gates to playfully learn how the very basic components of a computer work.

??? note "CODE"
    ``` python
    ...
    ```

!!! success ""
    Congrats, you are now good to go to create much more advanced editors and optimize them. ryvencore has much more features than I showed here. For that, see the [Features](../features/) section where you will find more detailed descriptions of all the internal systems, from save&load over stylus-and touch-support to execution flows. The world is yours, have fun!
