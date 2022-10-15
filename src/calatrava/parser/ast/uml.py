
from abc import (
    ABCMeta,
    abstractmethod,
)

import ast
from collections import namedtuple

from calatrava.parser.ast.node_visitors import (
    find_by_name,
    find_in_imports,
    collect_star_imports,
    collect_attr_long_name,
    BaseAssignCollector,
)
from calatrava.parser.ast.base import (
    BaseModule,
    BaseModuleMixins,
    BasePackage,
    BasePackageMixins,
    BasePackageManager,
    BasePackageManagerMixins,
)


PYTHON_PROTECTED_CLASSES = {
    'Exception', 'type', 'object', 'dict', 'list', 'tuple', 'set',
    'RuntimeError', 'UserWarning', 'RuntimeWarning', 'ValueError',
    'AttributeError',
}


class ModuleMixins(BaseModuleMixins):

    def __init__(self, ClassesVisitor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classes_visitor = ClassesVisitor(self)

        self.import_class_map = {}
        self.not_found = {}
        self.not_found_trial = {}

    @property
    def classes_ls(self):
        return self.classes_visitor.classes_ls

    @property
    def classes(self):
        return {class_.long_name: class_ for class_ in self.classes_ls}

    @property
    def _already_found(self):
        classes_ = {class_.name: class_ for class_ in self.classes_ls}
        return classes_ | self.import_class_map | self.not_found | self.not_found_trial

    def find_class(self, name, visited=()):
        # TODO: try to recode with pipeline? (specially to e.g. avoid checking stars)

        # visited only for possible recursion due to star imports
        if self in visited:
            return

        # try in already found
        class_ = self._already_found.get(name, None)
        if class_ is not None:
            return class_

        # try in python protected names
        if name in PYTHON_PROTECTED_CLASSES:
            return self.package.manager.find_class(name)

        # try in definitions
        node = find_by_name(self.root, ast.ClassDef, name)
        if node is not None:
            return self.classes_visitor.visit(node)

        # try in imports
        long_name = find_in_imports(
            self.root, name, self.long_name, self.is_init)
        if long_name is not None:
            class_ = self.package.manager.find_class(long_name)
            self.import_class_map[name] = class_
            return class_

        # try in start imports
        star_imports = collect_star_imports(self.root, self.long_name,
                                            self.is_init)
        if star_imports:
            if visited:
                visited.append(self)
            else:
                visited = [self]

            for star_import in star_imports:
                long_name = f'{star_import}.{name}'
                class_ = self.package.manager.find_class(
                    long_name, visited=visited)
                if class_ is not None:
                    self.import_class_map[name] = class_
                    return class_

        if not visited or (len(visited) == 1 and self in visited):
            # not found (e.g. assignment)
            class_ = DummyClass(name, self)

            self.package.manager.add_unknown_class(class_)
            self.not_found[name] = class_

            return class_

    def find_all_classes(self):
        class_nodes = [node for node in self.root.body if isinstance(node, ast.ClassDef)]
        return [self.classes_visitor.visit(node) for node in class_nodes]

    def update_inheritance(self):
        return self.classes_visitor.update_inheritance()


class Module(ModuleMixins, BaseModule):
    def __init__(self, long_name, package, ClassesVisitor):
        super().__init__(long_name=long_name, package=package,
                         ClassesVisitor=ClassesVisitor)


class PackageMixins(BasePackageMixins):

    def find_class(self, long_name, visited=()):
        long_name_ls = long_name.split('.')
        i = 0
        while True:
            i += 1

            if i > len(long_name_ls):
                raise Exception(f'Cannot find `{long_name}`')

            module_name = '.'.join(long_name_ls[:-i])
            if module_name in self.modules_names:
                class_name = '.'.join(long_name_ls[-i:])
                break
            elif module_name in self.extra_modules_names:
                return DummyClass(long_name)

        module = self.find_module(module_name)
        return module.find_class(class_name, visited=visited)

    def find_module_classes(self, module_name):
        module = self.find_module(module_name)

        return module.find_all_classes()

    def find_modules_classes(self, module_names):
        all_classes = []
        for module_name in module_names:
            all_classes.extend(self.find_module_classes(module_name))

        return all_classes

    def find_subpackage_classes(self, subpackage_name):
        module_names = [module_name for module_name in self.modules_names if module_name.startswith(subpackage_name)]
        return self.find_modules_classes(module_names)

    def find_all_classes(self):
        return self.find_modules_classes(self.modules_names)

    def find(self, import_):
        if import_ in self.subpackages_names:
            return self.find_subpackage_classes(import_)
        elif import_ in self.modules_names:
            return self.find_module_classes(import_)

        return self.find_class(import_)

    def update_inheritance(self):
        done = True
        for module in self.modules_ls:
            done_ = module.update_inheritance()
            if not done_:
                done = False

        return done

    def get_classes(self):
        classes = {}
        for module in self.modules_ls:
            classes |= module.classes

        return classes


def _get_classes_visitor(type_):
    accepted_types = [
        "basic", "basic-methods", "basic-attrs", "basic-attrs-methods",
    ]
    if type_ not in accepted_types:
        raise Exception("Unknown type_")

    if type_ == "basic":
        return lambda module: BasicClassesVisitor(module, Class=BasicClass)

    elif type_ == "basic-methods":

        class _Class(ClassMethodsMixins, BasicClass):
            pass

        class _ClassesVisitor(MethodsVisitorMixins, BasicClassesVisitor):
            def __init__(self, module, Class, Method):
                super().__init__(module=module, Class=Class, Method=Method)

        return lambda module: _ClassesVisitor(
            module, Class=_Class, Method=BasicMethod)

    elif type_ == "basic-attrs":
        class _Class(ClassAttrsMixins, BasicClass):
            pass

        class _ClassesVisitor(AttrsOnlyVisitorMixins, BasicClassesVisitor):
            def __init__(self, module, Class):
                super().__init__(module=module, Class=Class)

        return lambda module: _ClassesVisitor(module, Class=_Class)

    elif type_ == "basic-attrs-methods":
        class _Class(ClassAttrsMixins, ClassMethodsMixins, BasicClass):
            pass

        class _ClassesVisitor(AttrsVisitorMixins, MethodsVisitorMixins,
                              BasicClassesVisitor):
            def __init__(self, module, Class, Method):
                super().__init__(module=module, Class=Class, Method=Method)

        return lambda module: _ClassesVisitor(
            module, Class=_Class, Method=BasicMethod)


class Package(PackageMixins, BasePackage):
    def __init__(self, path, Module=Module, classes_visitor="basic", **kwargs):
        if classes_visitor is not None:
            kwargs.setdefault("ClassesVisitor", _get_classes_visitor(classes_visitor))

        Module_ = lambda long_name, package: Module(
            long_name, package, **kwargs)

        super().__init__(path=path, Module=Module_)


class PackageManagerMixins(BasePackageManagerMixins):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unknown_classes = {}

    def add_unknown_class(self, class_):
        self._unknown_classes[class_.long_name] = class_

    def find_class(self, long_name, visited=()):
        package = self._get_package(long_name)
        if package is None and visited:
            return
        elif package is None:
            class_ = self._unknown_classes.get(long_name,
                                               DummyClass(long_name))
            self.add_unknown_class(class_)
            return class_
        else:
            return package.find_class(long_name, visited=visited)

    def find_all_classes(self):
        classes = []
        for package in self.packages_ls:
            classes.extend(package.find_all_classes())

        return classes

    def find(self, import_):
        package = self._get_package(import_, raise_=True)
        return package.find(import_)

    def update_inheritance(self):
        while True:
            done = True
            for package in self.packages_ls:
                done_ = package.update_inheritance()
                if not done_:
                    done = False

            if done:
                break

    def get_classes(self):
        classes = {}
        for package in self.packages_ls:
            classes |= package.get_classes()

        classes |= self._unknown_classes

        return classes


class PackageManager(PackageManagerMixins, BasePackageManager):
    pass


TmpBase = namedtuple('TmpBase', ['name', 'is_import'])


class BaseClass(metaclass=ABCMeta):
    def __init__(self, name, module):
        self.name = name
        self.module = module

        self.children = []
        self.bases = []

    def __repr__(self):
        return f'<class: {self.long_name}>'

    @abstractmethod
    def long_name(self):
        pass

    @property
    def short_name(self):
        return self.name.split('.')[-1]

    @property
    def id(self):
        return self.long_name.replace('.', '_')

    @property
    def found(self):
        return self._found

    def add_child(self, child):
        self.children.append(child)

    def add_base(self, base):
        self.bases.append(base)
        base.add_child(self)


class DummyClass(BaseClass):
    def __init__(self, name, module=None):
        super().__init__(name, module)
        self._found = False

        self.is_python_type = name in PYTHON_PROTECTED_CLASSES

    @property
    def long_name(self):
        if self.module is not None:
            return f'{self.module.long_name}.{self.name}'

        return self.name

    @property
    def is_abstract(self):
        return False


class BasicClass(BaseClass):

    def __init__(self, name, module):
        super().__init__(name=name, module=module)

        self._tmp_bases = []

        self._found = True

    @property
    def long_name(self):
        return f'{self.module.long_name}.{self.name}'

    @property
    def is_abstract(self):
        for class_ in self.bases:
            if class_.long_name.startswith('abc.'):
                return True
        return False

    def add_tmp_bases(self, node):
        # ast.ClassDef

        bases = []
        for node in node.bases + node.keywords:
            if isinstance(node, ast.keyword):
                node = node.value

            if isinstance(node, ast.Name):
                name = node.id
                is_import = False
            elif isinstance(node, ast.Attribute):
                name = collect_attr_long_name(node)
                is_import = True
            else:  # unknown
                continue

            bases.append(TmpBase(name, is_import))

        self._tmp_bases.extend(bases)

    def get_tmp_bases(self):
        return self._tmp_bases

    def reset_tmp_bases(self):
        self._tmp_bases = []


class BasicClassesVisitor(ast.NodeVisitor):

    def __init__(self, module, Class):
        self.module = module

        self.classes_ls = []
        self.stack = []

        self.Class = Class

    @property
    def current_class(self):
        return self._get_last_from_stack(self.Class)

    @property
    def current_obj(self):
        return self.stack[-1]

    def _get_last_from_stack(self, type_):
        for obj in reversed(self.stack):
            if isinstance(obj, type_):
                return obj

    def _get_prefix_from_stack(self):
        if self.stack:
            return self.stack[-1].name
        else:
            return ''

    def visit_ClassDef(self, node):
        class_ = self.Class(self._get_obj_name(node), self.module)

        class_.add_tmp_bases(node)

        self.stack.append(class_)
        self.classes_ls.append(class_)

        for inner_node in node.body:
            self.visit(inner_node)

        self.stack.pop()

        return class_

    def _get_obj_name(self, node):
        name = node.name
        prefix = self._get_prefix_from_stack()
        if prefix:
            name = f'{prefix}.{name}'

        return name

    def update_inheritance(self):
        done = True
        for class_ in self.classes_ls:
            for tmp_base in class_.get_tmp_bases():
                done = False
                if tmp_base.is_import:
                    # complete import if import from
                    name_ls = tmp_base.name.split('.')
                    prefix = find_in_imports(
                        self.module.root, name_ls[0], self.module.long_name,
                        self.module.is_init)
                    name = f"{prefix}.{'.'.join(name_ls[1:])}"

                    base = self.module.package.manager.find_class(name)
                else:
                    base = self.module.find_class(tmp_base.name)

                class_.add_base(base)

            class_.reset_tmp_bases()

        return done


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


class BasicMethod:

    def __init__(self, name, class_):
        self.class_ = class_
        class_.add_method(self)

        self.name = name
        self.decorator_list = []

    @property
    def long_name(self):
        return f'{self.class_.module.long_name}.{self.name}'

    @property
    def short_name(self):
        return self.name.split('.')[-1]

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


class ClassesVisitorMixins(metaclass=ABCMeta):
    pass


class MethodsVisitorMixins(ClassesVisitorMixins):
    def __init__(self, Method, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Method = Method

    @property
    def current_method(self):
        return self._get_last_from_stack(self.Method)

    def visit_FunctionDef(self, node):
        func = self.Method(self._get_obj_name(node), self.current_class)
        func.add_decorators(node.decorator_list)

        self.stack.append(func)

        for inner_node in node.body:
            self.visit(inner_node)

        self.stack.pop()


class _AssignAttrsOnlyCollector(BaseAssignCollector):

    def visit_Attribute(self, node):
        self._target_names.append(collect_attr_long_name(node))


class _AssignNamesOnlyCollector(BaseAssignCollector):

    def visit_Name(self, node):
        self._target_names.append(node.id)


class AttrsOnlyVisitorMixins(ClassesVisitorMixins):
    # does not collect class attributes
    # collects everything in the class namespace

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attrs_collector = _AssignAttrsOnlyCollector()

    def visit_Assign(self, node):
        attrs_names = self._attrs_collector.collect_targets(node)

        for target_name in attrs_names:
            target_name_ls = target_name.split('.')
            self.current_class.add_attr(target_name_ls[1])


class AttrsVisitorMixins(ClassesVisitorMixins):
    # it will be incompatible with other `visit_Assign` mixins
    # needs MethodsVisitorMixins to work properly

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attrs_collector = _AssignAttrsOnlyCollector()
        self._cls_attrs_collector = _AssignNamesOnlyCollector()

    def visit_Assign(self, node):
        if isinstance(self.current_obj, BaseClass):
            cls_attrs_name = self._cls_attrs_collector.collect_targets(node)

            for target_name in cls_attrs_name:
                target_name_ls = target_name.split('.')

                if len(target_name_ls) == 1:
                    self.current_class.add_cls_attr(target_name)

        else:  # is a method
            attrs_names = self._attrs_collector.collect_targets(node)

            for target_name in attrs_names:
                target_name_ls = target_name.split('.')
                self.current_class.add_attr(target_name_ls[1])
