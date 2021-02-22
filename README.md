**ryvencore is not 100% ready yet, there's still some work to do**

Salut! rvencore is a Qt based framework for building flow-based visual scripting editors for Python. It comes from the Ryven project and will be the foundation for future Ryven versions amongst other editors. ryvencore lets you create Ryven-like editors which you then can optimize for specific domains.

### Installation

```
pip install ryvencore
```

### Features

- **load & save**
- **variables system** with registration mechanism to build nodes that automatically adapt to change of data
- **built in logging**
- **simple nodes system**
- **dynamic nodes registration mechanism** to register and unregister nodes at runtime
- **right click operations system for nodes**
- **you can add any Qt widgets to your nodes** (hence you could also embed your Python-Qt applications with GUI)
- **convenience GUI classes**
- **many different modifiable themes**
- **data *and* exec flow support**
- **stylus support for adding handwritten notes**
- **rendering flow images**
- **THREADING READY** [extremely experimental though]

Threading ready means that all internal communication between the abstract components and the GUI of the flows is implemented in a somewhat thread save way, so, while still having an intuitive API, it is compatible with applications that keep their abstract components in a separate thread. While this is currently a very experimental feature whose implementation will experience improvement in the future, the basic structure is already there and successful tests have been made. A lot of work went into this and I think it's of crucial importance since this opens the door to the world of realtime data processing.

I am very excited about this, but there is of course still room for improvement, currently especially regarding convenience GUI classes and touch support. For a more detailed overview visit the [docs page](https://leon-thomm.github.io/ryvencore/).
