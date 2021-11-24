
<p align="center">
  <img src="./docs/img/logo.png" alt="drawing" width="70%"/>
</p>

Python backend for graph-based processing, designed for flow-based/node-based visual scripting editors. It is the backbone of the [Ryven](https://github.com/leon-thomm/Ryven) project but it can be used for other applications as well.

If you are not already familiar with flow-based visual scripting and are looking for a specification, see [docs]().

### Installation

```
pip install ryvencore
```

from sources:
```
git clone https://github.com/leon-thomm/ryvencore
cd ryvencore
pip install .
```

### Dependencies

None! `ryvencore` runs completely on standard python modules, no additional libraries required, which makes it very compatible.

*I am therefore thinking about extending the implementation to compile with Cython. While the overhead produced by the internal graph representation compared to only executing python code specified in the nodes' `update_event` does not dominate, efficient Cython support might lead to speedup of another ~20%-40%.*

### Usage

Using `ryvencore` directly to run projects made with `ryvencore`-based editors, the following code example gives some intuition about the process:

```python
import ryvencore as rc
import json
import sys

if __name__ == '__main__':
    # get a working project file path
    if len(sys.argv) < 2:
        sys.exit('please provide a project file path')
    fpath = sys.argv[1]
    try:
        f = open(sys.argv[1])
        f.close()
    except FileNotFoundError:
        sys.exit('could not open file '+fpath)
    
    # read project file
    with open(fpath, 'r') as f:
        project: dict = json.loads(f.read())
    
    # run ryvencore
    session = rc.Session()
    session.load(project)

    # and now we can manually access all components, for example:
    scripts = session.scripts
    flow1 = scripts[0].flow
    my_node = flow1.nodes[-1]
    my_node.update()
```

### Main Features

`ryvencore` is rather small but already does some work for you

- **load & save**
- **variables system** with registration mechanism to build nodes that automatically adapt to change of data
- **built in logging**
- **simple nodes system**
- **dynamic nodes registration mechanism** to register and unregister nodes at runtime
- **actions system for nodes**
- **data *and* exec flow support**

For a more detailed overview, see the [docs]().
