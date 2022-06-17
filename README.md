
=========
calatrava
=========

`calatrava` is a Python code architecture analyzer, i.e. it builds [UML diagrams](https://en.wikipedia.org/wiki/Unified_Modeling_Language) (or something similar) for a given `class`, `module`, `subpackage`, or `package`.

It relies on [`findimports`](https://pypi.org/project/findimports/) (to parse import information), [`xlizard`](https://github.com/lpereira95/xlizard) (an adaptation of [`lizard`](https://pypi.org/project/lizard/) with a more powerful Python parser; to parse information about object definition), and [`graphviz`](https://pypi.org/project/graphviz/) do draw diagrams.


Installation
============

`calatrava` is not available in [PyPI](https://pypi.org/) yet (due to its imaturity). Therefore, install it with


```bash
pip install git+https://github.com/lpereira95/calatrava.git@master
```


If you also want to install requirements, do

```bash
pip install git+https://github.com/lpereira95/calatrava.git@master#egg=calatrava
```


Usage
=====

The most straighforward way to use `calatrava` is as a CLI tool ([`click`](https://pypi.org/project/click/) handles this). To check the available commands do:

```bash
calatrava --help
```

For most of the available commands (`classes`, `modules`, `subpackages`, `package`) the input takes the following form:


```bash
calatrava <command> <package_name> <package_dir> <args> -o <filename>
```


`<args>` is not specified because it depends on the particular command (moreover, `<args>` can be single or multiple):

* `classes`: class(es) import path(s)
* `modules`: module(s) import path(s)
* `subpackages`: subpackage(s) path(s)
* `package`: not applicable


To get more information about the expected parameters for a given command, do:


```bash
calatrava <command> --help
```


Examples
========

Let's examplify `calatrava` usage by exploring [`geomstats`](https://github.com/geomstats/geomstats).


Classes
-------

The following command:

```bash
calatrava classes $(GEOMSTATS_DIR) geomstats.geometry.spd_matrices.SPDMatrices
```


creates

![example_class.svg]https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_class.svg)


**Note**: do `export GEOMSTATS_DIR=<dirpath>` or replace `$(GEOMSTATS_DIR)` with a valid path.


To draw more classes, just add the corresponding import:

```bash
calatrava classes $(GEOMSTATS_DIR) geomstats.geometry.spd_matrices.SPDMatrices geomstats.geometry.spd_matrices.SPDMetricAffine
```

![example_classes.svg]https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_classes.svg)


Modules
-------

Similarly, for modules:


```bash
calatrava modules geomstats $(GEOMSTATS_DIR) geomstats.geometry.spd_matrices
```

![example_module.svg]https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_module.svg)


Follow the same procedure as above for several modules.


Subpackages
-----------


Similarly, for subpackages:

```bash
calatrava subpackages geomstats $(GEOMSTATS_DIR) geomstats.geometry
```

![example_subpackage.svg]https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_subpackage.svg)


Follow the same procedure as above for several modules.


Package
-------

Similarly, for packages:

```bash
calatrava package geomstats $(GEOMSTATS_DIR)
```

(For sanity, generated diagram will not be displayed. Try it out yourself!)



Which information is conveyed in a diagram?
===========================================

inheritance information