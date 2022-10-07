
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
    collect_assign_targets,
)
from calatrava.parser.ast.base import (
    BaseModule,
    BasePackage,
    BasePackageManager,
)


PYTHON_PROTECTED_CLASSES = (
    'Exception', 'type', 'object', 'dict', 'list', 'tuple', 'set',
)

# TODO: create factories
# TODO: concept of alias (then update alias?)


class ModuleMixins:

    def __init__(self, ClassesVisitor, **kwargs):
        super().__init__(**kwargs)
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

        if not visited:
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


class PackageMixins:

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
        module_names = [module_name for module_name in self.all_modules_names if module_name.startswith(subpackage_name)]
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
    if type_ == "basic":
        return lambda module: BasicClassesVisitor(module, Class=BasicClass)


class Package(PackageMixins, BasePackage):
    def __init__(self, path, Module=Module, classes_visitor="basic", **kwargs):
        if classes_visitor is not None:
            kwargs.setdefault("ClassesVisitor", _get_classes_visitor(classes_visitor))

        Module_ = lambda long_name, package: Module(
            long_name, package, **kwargs)

        super().__init__(path=path, Module=Module_)


class PackageManagerMixins:

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
            else:  # ast.Attribute
                name = collect_attr_long_name(node)
                is_import = True

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
                    base = self.module.package.manager.find_class(tmp_base.name)
                else:
                    base = self.module.find_class(tmp_base.name)

                class_.add_base(base)

            class_.reset_tmp_bases()

        return done


class Class(BasicClass):
    # TODO: probably via mixins?

    def __init__(self, name, module):
        super().__init__(name, module)

        self.attrs = []
        self.methods = []

    @property
    def all_attrs(self):
        return self.attrs + self.base_attrs

    @property
    def base_attrs(self):
        attrs = []
        for base in self.bases:
            attrs.extend(base.all_attrs)

        return attrs

    @property
    def all_methods(self):
        return self.methods + self.base_methods

    @property
    def base_methods(self):
        methods = []
        for base in self.bases:
            methods.extend(base.all_methods)
        return methods

    def add_attr(self, attr_name):
        self.attrs.append(attr_name)

    def add_local_var(self, var_name):
        self.cls_attrs.append(var_name)

    def add_method(self, method):
        self.methods.append(method)


class Method:

    def __init__(self, name, class_):
        self.class_ = class_
        class_.add_method(self)

        self.name = name
        self.local_vars = []
        self.decorator_list = []

    @property
    def long_name(self):
        return f'{self.class_.module.long_name}.{self.name}'

    @property
    def short_name(self):
        return self.name.split('.')[-1]

    def __repr__(self):
        # TODO: handle abstract methods

        if self.is_property:
            type_ = 'property'
        elif self.is_classmethod:
            type_ = 'classmethod'
        else:
            type_ = 'method'

        return f'<{type_}: {self.short_name}>'

    @property
    def is_property(self):
        return 'property' in self.decorator_list

    @property
    def is_classmethod(self):
        return 'classmethod' in self.decorator_list

    def add_local_var(self, var_name):
        self.local_vars.append(var_name)

    def add_decorators(self, decorator_list):
        for node in decorator_list:
            # TODO: rethink due to function?
            if isinstance(node, ast.Name):
                name = node.id
            else:  # ast.Attribute
                name = collect_attr_long_name(node)
            self.decorator_list.append(name)


class ClassesVisitor(BasicClassesVisitor):
    # TODO: probably via mixins?

    def __init__(self, module, Class):
        super().__init__(module, Class)

        self.Method = Method

    @property
    def in_class(self):
        # TODO: is it required?
        return isinstance(self.stack[-1], Class)

    @property
    def current_method(self):
        return self._get_last_from_stack(self.Method)

    def visit_Assign(self, node):
        current_class = self.current_class
        current_obj = self.current_obj

        target_names = collect_assign_targets(node)

        for target_name in target_names:
            target_name_ls = target_name.split('.')
            if len(target_name_ls) == 2 and target_name_ls[0] == 'self':
                current_class.add_attr(target_name_ls[1])
            elif len(target_name_ls) == 1:
                current_obj.add_local_var(target_name)

    def visit_FunctionDef(self, node):
        func = self.Method(self._get_obj_name(node), self.current_class)
        func.add_decorators(node.decorator_list)

        self.stack.append(func)

        for inner_node in node.body:
            self.visit(inner_node)

        self.stack.pop()
