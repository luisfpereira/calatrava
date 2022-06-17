
# calatrava


`calatrava` is a Python code architecture analyzer, i.e. it builds [UML diagrams](https://en.wikipedia.org/wiki/Unified_Modeling_Language) (or something similar) for a given `class`, `module`, `subpackage`, or `package`.

It relies on [`findimports`](https://pypi.org/project/findimports/) (to parse import information), [`xlizard`](https://github.com/lpereira95/xlizard) (an adaptation of [`lizard`](https://pypi.org/project/lizard/) with a more powerful Python parser; to parse information about object definition), and [`graphviz`](https://pypi.org/project/graphviz/) do draw diagrams.


## Installation


`calatrava` is not available in [PyPI](https://pypi.org/) yet (due to its imaturity). Therefore, install it with


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

For most of the available commands (`classes`, `modules`, `subpackages`, `package`) the input takes the following form:


```bash
calatrava <command> <package_name> <package_dir> <args> -o <filename>
```


`<args>` depends on the particular command and can be can be single or multiple):

* `classes`/`modules`/`subpackages`: class(es)/module(s)/subpackage(s) import path(s)
* `package`: not applicable


To get more information about the expected parameters for a given command, do:


```bash
calatrava <command> --help
```


## Examples

Let's examplify `calatrava` usage by exploring [`geomstats`](https://github.com/geomstats/geomstats).


### Classes


The following command:

```bash
calatrava classes $GEOMSTATS_DIR geomstats.geometry.spd_matrices.SPDMatrices
```


creates

![example_class.svg](https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_class.svg)


**Note**: do `export GEOMSTATS_DIR=<dirpath>` or replace `$GEOMSTATS_DIR` with a valid path.


To draw more classes, just add the corresponding import:

```bash
calatrava classes $GEOMSTATS_DIR geomstats.geometry.spd_matrices.SPDMatrices geomstats.geometry.spd_matrices.SPDMetricAffine
```

![example_classes.svg](https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_classes.svg)


### Modules

```bash
calatrava modules geomstats $GEOMSTATS_DIR geomstats.geometry.spd_matrices
```

![example_module.svg](https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_module.svg)


(Follow the same procedure as above for several modules.)


### Subpackages


```bash
calatrava subpackages geomstats $GEOMSTATS_DIR geomstats.geometry
```

![example_subpackage.svg](https://raw.githubusercontent.com/lpereira95/calatrava/master/images/example_subpackage.svg)


(Follow the same procedure as above for several subpackages.)


### Package

```bash
calatrava package geomstats $GEOMSTATS_DIR
```

(For sanity, the generated diagram will not be displayed. Try it out yourself!)



## Which information is conveyed in a diagram?


`calatrava` builds inheritance trees. (Composition information is not easy to gather in a dynamic language and is therefore ignored.) Some (hopefully) useful information:

* Arrows represent inheritance.
* Inheritance coming from external packages is ignored (e.g. if your class derives from [`sklearn.base.Estimator`](https://scikit-learn.org/stable/modules/generated/sklearn.base.BaseEstimator.html#sklearn.base.BaseEstimator), this relationship will be ignored). 
* Trees are built bottom-up, meaning we start with a desired class (e.g. the one specified with `classes` command) and create records for all the classes from which it inherits directly or from which parents (and grandparents, and...) inherit from.
* Each record is split into two boxes: the first contains attributes, the second contains methods.
* (For now) properties are treated as methods.
* Attributes or methods that are inherited are prefixed by `-`.
* Attributes or methods that are overriden or defined for the first time are prefixed by `+`.