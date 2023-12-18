
from abc import ABCMeta
import ast

from calatrava.parser.ast.node_visitors import collect_attr_long_name

# TODO: check overlap with already defined objects


class BasicClass:

    def __init__(self, name, is_abstract=False):
        self.name = name

        self.children = []
        self.bases = []

        self.methods = []

        self.found = True
        self.is_abstract = is_abstract

    def add_child(self, child):
        self.children.append(child)

    def add_base(self, base):
        self.bases.append(base)
        base.add_child(self)

    @property
    def id(self):
        return self.long_name.replace('.', '_')

    @property
    def long_name(self):
        return self.name


class ClassMixins(metaclass=ABCMeta):
    pass


class ClassMethodsMixins(ClassMixins):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.methods = []

    @property
    def all_methods(self):
        return self.methods + self.base_methods

    @property
    def base_methods(self):
        methods = []
        for base in self.bases:
            if base.found:
                methods.extend(base.all_methods)
        return methods

    def add_method(self, method):
        self.methods.append(method)


class ClassAttrsMixins(ClassMixins):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs = []
        self.cls_attrs = []

    @property
    def all_attrs(self):
        return self.attrs + self.base_attrs

    @property
    def base_attrs(self):
        attrs = []
        for base in self.bases:
            if not base.found:
                continue

            attrs.extend(base.all_attrs)

        return attrs

    def add_attr(self, attr_name):
        self.attrs.append(attr_name)

    def add_cls_attr(self, var_name):
        self.cls_attrs.append(var_name)


class Class(ClassAttrsMixins, ClassMethodsMixins, BasicClass):
    pass


class BasicMethod:

    def __init__(self, name, class_, decorator_list=None):
        self.class_ = class_
        class_.add_method(self)

        self.name = name

        self.decorator_list = decorator_list if decorator_list else []

    @property
    def short_name(self):
        return self.name

    @property
    def is_property(self):
        return 'property' in self.decorator_list

    @property
    def is_classmethod(self):
        return 'classmethod' in self.decorator_list

    @property
    def is_abstractmethod(self):
        return 'abstractmethod' in self.decorator_list or 'abc.abstractmethod' in self.decorator_list

    @property
    def is_setter(self):
        return f"{self.short_name}.setter" in self.decorator_list

    def __repr__(self):

        if self.is_property:
            type_ = 'property'
        elif self.is_classmethod:
            type_ = 'classmethod'
        elif self.is_abstractmethod:
            type_ = 'abstractmethod'
        elif self.is_setter:
            type_ = 'setter'
        else:
            type_ = 'method'

        return f'<{type_}: {self.short_name}>'

    def add_decorators(self, decorator_list):
        for node in decorator_list:
            if isinstance(node, ast.Name):
                name = node.id
            else:  # ast.Attribute
                name = collect_attr_long_name(node)
            self.decorator_list.append(name)
