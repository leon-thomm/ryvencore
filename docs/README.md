The documentation is based on Sphinx, the documentation sources are in the `source` folder.
This documentation is automatically built from the ryvencore source code and deployed to GitHub Pages by GitHub Actions
whenever the main branch is pushed to. To test locally, proceed as follows:

**move into `docs`**

```
$ cd docs
```

**create and activate virtual environment**

```
$ python -m venv venv
$ source venv/bin/activate
```

**install requirements**

```
$ pip install -r requirements.txt
```

**install ryvencore from sources**

```
cd ..
pip install .
cd docs
```

**build the documentation**

```
$ sphinx-build source build
$ firefox ./build/index.html
```