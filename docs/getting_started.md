# Installation

## Requirements

You need a recent Python version, preferably 3.9+. The only internal dependency of ryvencore right now is `PySide2` which will be installed automatically.

## Installing

`pip install ryvencore` will install the package.

# First Editor

!!! info
    You can copy the full example code at the end of this page.

First, import ryvencore

``` python
import ryvencore.ryvencore as rc
```

## Overall Structure

The main interface to the package is the **Session** class, which you usually want to create one instance of per application. The constructor already gives plenty of options for configurations, but we can leave everything as default for now.

``` python
my_session = Session()
```

Now you need to create a **Script**. A script contains **variables**, **logs**, as well as the actual **flow** that you are looking for.

``` python
script = my_session.create_new_script('fancy title', flow_size=[800, 500])
```

With the `flow_size` you can set the pixel size of the flow that will be created. To access the actual flow, just reference the field `script.flow` directly. The flow itself is a `QGraphicsView` subclass, which is a GUI class of Qt, so you can directly embed it into your window.

## Setting Up a Window

This is not a complete tutorial on getting started with Qt for Python, but setting up a basic GUI structure is quite simple.

``` python
import ryvencore.ryvencore as rc
import sys
from PySide2.QtWidgets import QMainWindow, QApplication

if __name__ == "__main__":

    # create a QApplication and a MainWindow
    # the QMainWindow will be subclassed later
    app = QApplication()
    mw = QMainWindow()

    # creating the session
    session = rc.Session()
    
    # creating a script
    script = session.create_script('ueli', flow_size=[800, 500])

    # and setting the flow widget as the windows central widget
    mw.setCentralWidget(script.flow)
    
    mw.show()
    sys.exit(app.exec_())
```

And there we go, this is everything you need to create and show a window containing a fully functional flow. You can left click into the scene to see a node selection widget pop up. Well, there isn't any content yet to use, so let's add that.

## Nodes

In ryvencore the nodes system works like this:

A full node consists of two parts:

- the **Node** *object*
- the **NodeInstance** *class*

The Node stores general information and the NodeInstance class is what will actually be instanciated when you place the node in the flow. This way you have full control. We will see in a second how to program the NodeInstance class.

!!! important "Notice"
    You can put any code into your node's NodeInstance class, no limits! You can define additional classes, use external packages, basically everything you can do in a python class.

The session stores the nodes. Before you can use a node in a flow, you must register it in the session. In the code above, you would add the following code at line 14:

``` python
session.register_nodes( list_of_nodes )
```

!!! hint
    You can register nodes at any time! This enables dynamic import mechanisms as in Ryven.

### NodeInstance

The first thing you want to think about is your node's NodeInstance class, where you define the whole functionality. For a detailed description of the members, take a look into the [API reference](/api/). We'll just create a very simple print node, which prints the data at the input every time it updates.

``` python
class PrintNI(rc.NodeInstance):

    # we could also skip the constructor in this case
    def __init__(self, params):
        rc.NodeInstance.__init__(self, params)

    def update_event(self, input_called=-1):
        # get data from first input
        data = self.input(0)
        print(data)
```

Make your class derive from `rc.NodeInstance` and then enhance it the way you like. The `update_event` is the important part, it get's triggered every time the node is supposed to update.

!!! note
    While most flow-based visual scripting software out there implements either the approach of *execution-flows* or *data-flows*, ryvencore implements them both. That's what the `input_called`-parameter is for, you use it when creating nodes for execution-flows. But I don't want to dive into the differences here, for now I assume we just want dataflows.

### Node

As described, last thing to do is registering the node, which is quite straight forward

``` python
# registering one node
session.register_node(
    rc.Node(
        title='Print',
        description='prints your data.',
        node_inst_class=PrintNI,
        inputs=[
            rc.NodePort('data')
        ],
        color='#A9D5EF'
    )
)
```

!!! tip
    Use a code editor that previews the available parameters with default values.

!!! warning
    NodePort might get renamed soon to NodeInput and NodeOutput

There we go, this is everything you need. Now, I will just add another node which generates a random number in a given range, so we have something to print.

### Another Node

``` python
from random import random

class RandNI(rc.NodeInstance):
    def update_event(self, input_called=-1):
        # random between 0 and value at input
        val = random()*self.input(0)
        # self.set_output_val is an API call, see reference
        self.set_output_val(0, val)
```

``` python
session.register_node(
    rc.Node(
        title='Rand',
        description='generates random float',
        node_inst_class=RandNI,
        inputs=[
            rc.NodePort('data', widget='std line edit m', widget_pos='besides')
        ],
        outputs=[
            rc.NodePort('data')
        ],
        color='#fcba03'
    )
)
```

Note the `widget`-and `widget_pos`-parameters in the NodePort which I explain in the following section.

### Input Widgets

Data inputs can have widgets (like input fields aka LineEdits). The only restriction for defining an InputWidget is that it has to be a `QWidget`. Custom such input widgets can be registered by listing them in the `NodePort`'s `input_widgets`-parameter (see [API](reference)). Usually, however, the builtin classes provided by ryvencore are sufficient. For example the following line of code creates an input field of the builtin type *std line edit* of size m.

``` python
rc.NodePort('data', widget='std line edit m', widget_pos='besides')
```

## Finishing

Now you already have a small editor with all major features. You can place the two nodes, connect them by mouse, type somethin into the randome-NodeInstance's input field and hit enter to trigger the update. It will then update and the `self.set_output_val()` call will trigger the connected print-NodeInstance to update.

Of course there is much more that you can do. For example you can change the flow theme.

``` python
session = rc.Session(flow_theme_name='dark tron')
```

Currently (probably) available flow themes are *dark tron*, *dark std*, *ghostly*, *blender*, *easy*, *peasy*, and *ueli*.

You can also change the performance mode to *fast*, you can disable animations and so on...

``` python
session = rc.Session(
    flow_theme_name='dark tron', 
    flow_performance_mode='fast',
    animations_enabled=False
)
```

!!! success "Congrats!"
    Congrats, you are good to go to create much more advanced editors and optimize them. ryvencore has much more features than I showed here. For that, see the [Features](/features/) section where you will find more detailed descriptions of all the internal systems, from save&load over stylus-and touch-support to execution flows. The world is yours, have fun :)

??? note "CODE"
    ``` python
    import src.ryvencore as rc
    import sys
    from PySide2.QtWidgets import QMainWindow, QApplication
    from random import random


    class PrintNI(rc.NodeInstance):

        # we could also skip the constructor in this case
        def __init__(self, params):
            rc.NodeInstance.__init__(self, params)

        def update_event(self, input_called=-1):
            # get data from first input
            data = self.input(0)
            print(data)


    class RandNI(rc.NodeInstance):
        def update_event(self, input_called=-1):
            # random between 0 and value at input
            val = random()*self.input(0)
            # self.set_output_val is an API call, see reference
            self.set_output_val(0, val)


    if __name__ == "__main__":

        # create a QApplication and a MainWindow
        # the QMainWindow will be subclassed later
        app = QApplication()
        mw = QMainWindow()

        # creating the session
        session = rc.Session(flow_theme_name='peasy')

        # registering one node
        session.register_nodes(
            [
                rc.Node(
                    title='Print',
                    description='prints your data.',
                    node_inst_class=PrintNI,
                    inputs=[
                        rc.NodePort('data', widget='std line edit m')
                    ],
                    color='#A9D5EF'
                ),
                rc.Node(
                    title='Rand',
                    description='generates random float',
                    node_inst_class=RandNI,
                    inputs=[
                        rc.NodePort('data', widget='std line edit m', widget_pos='besides')
                    ],
                    outputs=[
                        rc.NodePort('data')
                    ],
                    color='#fcba03'
                )
            ]
        )

        # creating a script
        script = session.create_script('ueli', flow_size=[800, 500])

        # and setting the flow widget as the windows central widget
        mw.setCentralWidget(script.flow)

        mw.show()
        sys.exit(app.exec_())
    ```