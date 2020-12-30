# API Reference

## [class] `Session`

A session is the top-most interface to your contents. Usually you will want to create one session per application instance, but you could create multiple ones to have different independent environments in one application.

### Signals

The following signals are yousful if you use custom widgets for listing the scripts. You can connect these signals to the corresponding GUI classes to make your GUI adapt.

| Parameter                         | Type                                      | Description                               |
| --------------------------------- | ----------------------------------------- | ----------------------------------------- |
| `new_script_created`              | `Script`                                  | Triggered when a new script is created.   |
| `script_renamed`                  | `Script`                                  | Triggered when a script has been renamed. |
| `script_deleted`                  | `Script`                                  | Triggered when a script has been deleted. |

### Attributes

| Parameter                         | Description                               |
| --------------------------------- | ----------------------------------------- |
| `scripts`                         | A list of all scripts.                    |
| `nodes`                           | A list of all registered nodes.           |
| `design`                          | The session's `Design` object.            |

### Methods

#### `Session.Session(flow_performance_mode: str = 'pretty', animations_enabled: bool = True, flow_theme_name: str = 'ueli', flow_data_conn_class=DataConnection, flow_exec_conn_class=ExecConnection, project: dict = None)`

| Parameter                         | Description                               |
| --------------------------------- | ----------------------------------------- |
| `flow_performance_mode`           | `'pretty'` or `'fast'` |
| `animations_enabled`              | NodeInstances blink on update if enabled |
| `flow_theme_name`                 | The name of the used flow theme. See `Session.design.available_flow_themes()`. |
| `flow_data_conn_class`            | (not official yet) You might be able to customize connections in the future (for adding stuff like weights, for instance). |
| `flow_exec_conn_class`            | (not official yet) You might be able to customize connections in the future (for adding stuff like weights, for instance). |
| `project`                         | A project config dict for directly causing a `Session.load()` call. |

#### `Session.register_node(node: Node)`

Before you can use a node in a session's scripts' flows, you need to register them.

!!! note
    You can register nodes at any time!

??? example
    ``` python
    my_session.register_node(
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
    See class `Node`.

#### `Session.register_nodes(nodes: [Node])`

Convenience class for registering a list of nodes at once.

#### `Session.create_script(title: str, flow_size: list = None, flow_parent=None, create_default_logs=True) -> Script`

| Parameter                         | Description                               |
| --------------------------------- | ----------------------------------------- |
| `title`                           | title of the new script                   |
| `flow_size`                       | the pixel size of the flow in format `[x, y]` |
| `flow_parent`                     | You usually won't need this, but if you want your flow to be a child of the window or some other widget, pass it here. |
| `create_default_logs`             | Indicates whether the script's default logs (*Global* and *Errors*) should get created. You can also do this later manually via `my_script.logger.create_default_logs()`. |

Creates and returns a script which triggers the `Session.new_script_created` signal.

#### `Session.rename_script(script: Script, title: str)`

Renames a script which triggers the `Session.script_renamed` signal.

#### `Session.delete_script(script: Script)`

Deletes a script which triggers the `Session.script_deleted` signal.

#### `Session.load(project: dict) -> bool`

Loads a project, which meands creating all scripts saved in the provided project dict and building all their contents including the flows.

#### `Session.serialize() -> list`

Returns a list with *config data* of all scripts for saving the project.

!!! warning
    Method signature might get changed

#### `Session.all_node_instances() -> [NodeInstance]`

Returns a list of all NodeInstance objects from all flows of the session's scripts, which can be useful for analysis.

#### `Session.set_stylesheet(s: str)`

Sets the session's stylesheet which can be accessed by NodeInstances and their widgets.

## [class] `Debugger`

The debugger class just provides another way to print, such that the additional info is disabled by default but can be enabled for troubleshooting. No official API *yet*.

## [class] `Script`



## [class] `Logger`

## [class] `Log`

## [class] `VarsManager`

## [class] `Flow`

## [class] `Node`

### Methods

#### `Node.Node(title: str, node_inst_class, inputs: [NodePort] = [], input_widgets: dict = {}, outputs: [NodePort] = [], description: str = '', style: str = 'extended', color: str = '#A9D5EF', widget=None, widget_pos: str = 'below ports', type_: str = '')`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `title`               | The node's title which will be displayed by the widgets and the NodeInstances. |
| `node_inst_class`     | A reference to your node's custom NodeInstance subclass.   |
| `inputs`              | A list of `NodePort`s. |
| `input_widgets`       | A dict of type `{str : class}`. The string will be the identifier, the class will get instanciated when an input with the identifier given as widget name is instanciated. |
| `outputs`             | A list of `NodePort`s. Note that outputs can't have widgets. |
| `description`         | Will be displayed when hovering above the NodeInstance with the mouse. |
| `style`               | `'extended'` or `'small'` |
| `color`               | The theme color used by the NodeInstances |
| `widget`              | A reference to the class for the `main_widget` if used. |
| `widget_pos`          | `'below ports'` or `'between ports'` |
| `type_`               | You can use this for grouping your nodes into categories. |

??? example
    ``` python
    Node(
        title='Print',
        description='prints your data.',
        node_inst_class=PrintNI,
        inputs=[
            rc.NodePort('data', widget='std line edit m')
        ],
        color='#A9D5EF'
    )
    ```

## [class] `NodePort`

### Methods

#### `NodePort.NodePort(type_: str = 'data', label: str = '', widget: str = None, widget_pos: str = 'besides')`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `type_`               | `'data'` or `'exec'` |
| `label`               | Label string displayed by the NodeInstances. Can be empty. |
| `widget`              | String identifier for an input widget. There are builtin input widgets and you can define your own and use them here if you provided them in `Node.Node(input_widgets=...)`. |
| `widget_pos`          | `'besides'` or `'below'` means besides or below the port pin. |

??? example
    ``` python
    rc.NodePort('data', widget='std line edit m', widget_pos='besides')
    ```
    Right now, available builtin widgets are: `std spin box`, `std line edit [s/m/l]` (like shown above), `std line edit [s/m/l] r` additionally resizes horizontally according to content, and `std line edit [s/m/l] r nb` resizes and has an invisible border.

## [class] `NodeInstance`

The `NodeInstance` class gets subclassed for every node.

### Subclassed Methods

#### `NodeInstance.NodeInstance(params)`

The constructor can be skipped if it isn't needed in the subclass. Otherwise, you would do something like this:

??? example
    ``` python
    class MyNodeInstance(rc.NodeInstance):
        def __init__(self, params):
            super(MyNodeInstance, self).__init__(params)

            self.special_actions['do something'] = {'method': self.do_sth_method}

            # and some custom attributes ...
            self.var_name = ''
            self.temp_var_val = None
    ```

#### `NodeInstance.update_event(input_called=-1)`

Triggered when the NodeInstance updates, usually through `NodeInstance.update()`. The node's functionality is defined here.

??? example
    A *arr get* NodeInstance's update event could look like this:
    ``` python
    def update_event(self, input_called=-1):
        arr = self.input(0)
        index = self.input(1)
		self.set_output_val(0, arr[index])
    ```

#### `NodeInstance.get_data()`

In this method, you need to provide all your internal data that define's your NodeInstance's current state (if there are different states). Usually you want to create a dict and put all your attributes *in JSON compatible format* in it, return it, and do the reverse in `NodeInstance.set_data(data)` (see below). The reason this method exists is that not all internal, potentially state defining attributes are serializable by something like `pickle` (Qt objects for instance).

Most simpler NodeInstances don't have states.

??? example
    Example for a *+* NodeInstance with a dynamic number of inputs, which can be changed by the user.
    ``` python
    def get_data(self):
        data = {'num inputs': self.num_inputs}
        return data
    ```

#### `NodeInstance.set_data(data)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `data`                | Holds the exact value you returned in `NodeInstance.get_data()`. |

Here you do the reverse of what you did in `NodeInstance.get_data()`.

!!! important
    Note that all ryvencore internal objects, such as the `special_actions` dict, **as well as inputs and outputs** get saved and restored automatically by ryvencore exactly as they were when the flow was saved. So, if you added some inputs for example, don't add them again manually in `set_data()` according to your attribute which indicates how many you added, this happens automatically.

??? example
    ``` python
    def set_data(self, data):
        self.num_inputs = data['num inputs']
    ```

#### `NodeInstance.remove_event()`

Triggered when the NodeInstance is removed from the scene. Note that this action might be undone by an undo operation by the user, in this case the exact NodeInstance object will just be placed in the scene again to not lose any data.

??? example
    Example from a *clock* NodeInstance running a timer in a separate thread. Of course this thread should get stopped when the NodeInstance is removed.
    ``` python
    def remove_event(self):
        self.timer.stop()
    ```

### Builtin Methods

#### `NodeInstance.update(input_called=-1, output_called=-1)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `input_called`        | If the NodeInstance is active (has exec inputs), you might want to pass the input the update is supposed to refer to. |
| `output_called`       | `output_called` is used to indicate that, in an execution flow, a request for data of an output has been made. You probably won't ever want to use this. |

Triggers an update event.

#### `NodeInstance.input(index: int)`

Returns the data that is at the input with given index. If the input is not connected, the input will return the widget's data (if it has a widget), otherwise it will return the data at the connected output of another NodeInstance. In all other cases, it returns `None`.

#### `NodeInstance.exec_output(index: int)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `index`               | Total index of the output.  |

For active (exec) nodes. Executes the output with given index.

#### `NodeInstance.set_output_val(index: int, val)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `index`               | Total index of the output. |
| `val`                 | The data that gets set at the output. This can be anything. |

In dataflows, this causes update events in all connected NodeInstances. This way, change of data is farward propagated through all NodeInstances that depend on it.

#### `NodeInstance.new_log(title: str) -> Log`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `title`               | The log's displayed title. |

Creates and returns a new log, owned by the NodeInstance.

#### `NodeInstance.disable_logs()`

Disables all logs owned by the NodeInstance. The convenience Log widget ryvencore provides then can be hidden. All logs owned by a NodeInstance automatically get disabled when the NodeInstance is removed.

#### `NodeInstance.enable_logs()`

Enabled all logs owned by the NodeInstance. The convenience Log widget ryvencore provides then shows the widget again, in case it has been hidden after it was disabled. All logs owned by a NodeInstance automatically get enabled again when a removed NodeInstance is restored through an undo operation.

#### `NodeInstance.log_message(msg: str, target: str)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `msg`                 | The message as string. |
| `target`              | `'Global'` or `'Errors'`. Refers to one of the script's default logs. |

#### `NodeInstance.update_shape()`

Causes recompilation of the whole shape.

#### `NodeInstance.create_new_input(type_: str = 'data', label: str = '', widget_name=None, widget_pos='besides', pos=-1)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `type_`               | `'data'` or `'exec'` |
| `label`               | The input's displayed label string. |
| `widget_name`         | The name an input widget has been registered under. `None` means no widget is used. |
| `widget_pos`          | `'besides'` or `'below'` |
| `pos`                 | The index this input should be inserted at. `-1` means appending at the end. |
<!-- | `config`              | The message as string. | -->

#### `NodeInstance.delete_input(i)`

Deletes the input at index `i`. All existing connections get removed automatically.

!!! warning
    Parameter signature might get changed soon

#### `NodeInstance.create_new_output(type_: str = 'data', label: str = '', pos=-1)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `type_`               | `'data'` or `'exec'` |
| `label`               | The output's displayed label string. |
| `pos`                 | The index this output should be inserted at. `-1` means appending at the end. |

#### `NodeInstance.delete_output(o)`

Deletes the output at index `o`. All existing connections get removed automatically.

!!! warning
    Parameter signature might get changed soon

#### `NodeInstance.session_stylesheet() -> str`

Returns the current session's stylesheet. This should be used for custom widgets to match the window's style. See `Session.register_stylesheet()`.

#### `NodeInstance.get_var_val(name: str)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `name`                | script variable's name |

Returns the current value of a script variable and `None` if it couldn't be found.

#### `NodeInstance.set_var_val(name: str, val)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `name`                | script variable's name |
| `val`                 | the variable's value |

Sets the value of a script variable and causes all registered receivers to update (see below).

#### `NodeInstance.register_var_receiver(name: str, method)`

| Parameter             | Description                               |
| --------------------- | ----------------------------------------- |
| `name`                | script variable's name |
| `method`              | a *reference* to the receiver method |

Registers a method as receiver for changes of script variable with given name.

??? example
    ``` python
    # connect to variable changes
    # self.var_val_updated refers to the receiver method
    self.register_var_receiver('x', self.var_val_updated)
    self.used_variable_names.append('x')
    ```

#### `NodeInstance.unregister_var_receiver(name: str)`

Unregisters a previously registers variable receiver. See `NodeInstance.register_var_receiver()`.











<!-- [Edit this page on GitHub](https://github.com/leon-thomm/Ryven){: .md-button } -->