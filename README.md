
# calatrava


[`calatrava`](https://en.wikipedia.org/wiki/Santiago_Calatrava) is a Python code architecture analyzer, i.e. it builds [UML diagrams](https://en.wikipedia.org/wiki/Unified_Modeling_Language) (or something similar) for classes, modules, subpackages, packages, or any combination of the former.

It relies on its own parser implementation (built on top of `ast`) to parse information about object definitions, and [`graphviz`](https://pypi.org/project/graphviz/) to draw diagrams. It is meant to be modular, so it should be relatively straightforward to plug-in different parsers and/or diagram creators.


## Installation

`calatrava` is not available in [PyPI](https://pypi.org/) yet (it will be soon). Therefore, install it with


```bash
pip install git+https://github.com/lpereira95/calatrava.git@master
```


If you also want to install requirements, do

```bash
pip install git+https://github.com/lpereira95/calatrava.git@master#egg=calatrava
```


## Usage

The most straighforward way to use `calatrava` is as a CLI tool ([`click`](https://pypi.org/project/click/) handles this). To check the available commands do:

```bash
calatrava --help
```

To get more detailed information for a given command do:

```bash
calatrava <command> --help
```


### `calatrava uml`

A basic usage of `calatrava uml` is:

```bash
calatrava uml <args> --config <config_file>
```

`<args>` is a variadic input argument that must contain package(s) location(s) (package name may be enough for installed packages). Additionally, valid import expressions may be passed: this tells `calatrava` to look uniquely to the specified import (being it a class, module, or subpackage).


`<config_file>` is a `json` configuration file that specifies the record creator (controls the looks of the output diagram) and filters. Filters remove (or keep) specific classes. There's plenty of filters already defined, but you can also define your owns. If a configuration file is not specified, then the global configuration file is used (must be stored in `~/.calatrava/config.json`). If it does not exist, then default values are used.


## Examples

There's plenty of examples available [here](https://calatrava.readthedocs.io/en/latest/examples.html).

Still, let's examplify `calatrava` usage by exploring [`geomstats`](https://github.com/geomstats/geomstats).


### Classes


The following command:

```bash
calatrava uml $GEOMSTATS_DIR geomstats.geometry.spd_matrices.SPDMatrices
```


creates

![example_class.svg](https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_class.svg)


**Note**: do `export GEOMSTATS_DIR=<dirpath>` or replace `$GEOMSTATS_DIR` with a valid path.


To draw more classes, just add the corresponding import:

```bash
calatrava uml $GEOMSTATS_DIR geomstats.geometry.spd_matrices.SPDMatrices geomstats.geometry.spd_matrices.SPDMetricAffine
```

![example_classes.svg](https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_classes.svg)


### Modules

```bash
calatrava uml $GEOMSTATS_DIR geomstats.geometry.spd_matrices
```

![example_module.svg](https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_module.svg)


(Follow the same procedure as above for several modules.)


### Subpackages


```bash
calatrava uml $GEOMSTATS_DIR geomstats.geometry
```

![example_subpackage.svg](https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_subpackage.svg)


(Follow the same procedure as above for several subpackages.)


### Package

```bash
calatrava uml $GEOMSTATS_DIR
```

(For sanity, the generated diagram will not be displayed. Try it out yourself!)



## Which information is conveyed in a diagram?


`calatrava` builds inheritance trees. (Composition information is not easy to gather in a dynamic language and is therefore ignored.) Some (hopefully) useful information:

* Arrows represent inheritance.
* Inheritance coming from external packages is ignored (e.g. if your class derives from [`sklearn.base.Estimator`](https://scikit-learn.org/stable/modules/generated/sklearn.base.BaseEstimator.html#sklearn.base.BaseEstimator), this relationship will be ignored), unless the path to the external package is explicitly given.
* Trees are built bottom-up, meaning we start with a desired class (e.g. the one specified with an import) and create records for all the classes from which it inherits directly or from which parents (and grandparents, and...) inherit from.
* Each record is split into two boxes: the first contains attributes, the second contains methods. Other options may split it in four (also class attributes and properties).
* Attributes or methods that are inherited are prefixed by `-`.
* Attributes or methods that are overriden or defined for the first time are prefixed by `+`.