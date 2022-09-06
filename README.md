
<p align="center">
  <img src="./docs/img/logo.png" alt="drawing" width="70%"/>
</p>

An experimental Python library for graph-based processing, designed for flow-based/node-based visual scripting editors. While it is the backbone of the [Ryven](https://github.com/leon-thomm/Ryven) project, it can very much be used in other contexts as well.

While ryvencore is written purely in Python, with not a single dependency it is very lightweight and highly compatible. It can be compiled with Cython, see the `setup_cython.py` file. The performance seems comparable so far, but the code hasn't been optimized for Cython yet, so there might be a lot of potential. Please consider contributing. Pyodide provides a WebAssembly port of ryvencore.

[//]: # (If you are not familiar with flow-based visual scripting and are looking for a specification, see [here]&#40;https://leon-thomm.github.io/ryvencore-qt/&#41;.)

### Installation

```
pip install ryvencore
```

or from sources:
```
git clone https://github.com/leon-thomm/ryvencore
cd ryvencore
pip install .
```

### Usage

As an experimental library, the API is not stable and small breaking changes over time should be expected. There is no maintained usage guide, but the code is documented and auto-generated docs are available [here](https://leon-thomm.github.io/ryvencore/).

A small example:

```python
import ryvencore as rc
import json
import sys

if __name__ == '__main__':
    # project file path
    fpath = sys.args[1]
    
    # read project file
    with open(fpath, 'r') as f:
        project: dict = json.loads(f.read())
    
    # run ryvencore
    session = rc.Session()
    session.load(project)

    # now we can access all components, for example:
    
    # get the first flow
    scripts = session.scripts
    flow1 = scripts[0].flow
    
    # and the last node that was created
    my_node = flow1.nodes[-1]
    
    # and execute it
    my_node.update()
```

### Main Features

- **load & save** into and from JSON-compatible dictionaries
- **variables system** with update mechanism to build nodes that automatically adapt to change of data
- **built in logging** based on python's `logging` module
- **powerful nodes system** which lets you do anything, simple and unrestricted
- **dynamic nodes registration mechanism** to register and unregister nodes at runtime
- **actions system for nodes**
- **data *and* exec flow support** - unlike lots of other solutions out there, ryvencore supports exec flows

For a more detailed overview, see the [docs](https://leon-thomm.github.io/ryvencore-qt/#/features).
