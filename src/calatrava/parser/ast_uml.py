
import ast
from pathlib import Path
import os
import tokenize
import glob
from collections import namedtuple


def find_by_name(root, type_, name):
    for node in ast.walk(root):
        if isinstance(node, type_) and node.name == name:
            return node


def find_in_imports(root, search_name):
    # TODO: need to move to node visitor?

    for node in ast.walk(root):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        for name in node.names:
            if search_name == name.name or search_name == name.asname:
                if isinstance(node, ast.Import):
                    # TODO: is this enough?
                    return name.name
                else:
                    # TODO: handle local imports
                    return f'{node.module}.{name.name}'


class ModuleVisitor:

    def __init__(self, module):
        self.module = module
        self.class_visitor = ClassVisitor(module)

        self.root = self._load_root()

        self.import_class_map = {}

    @property
    def classes(self):
        return self.class_visitor.classes

    def _load_root(self):
        with tokenize.open(self.module.path) as file:
            root = ast.parse(file.read(), self.module.path)

        return root

    def find_class(self, name):
        # try in existing
        class_ = self.module.classes.get(name, None)
        if class_ is not None:
            return class_

        # try in import map
        class_ = self.import_class_map.get(name, None)
        if class_ is not None:
            return class_

        # try in definitions
        node = find_by_name(self.root, ast.ClassDef, name)

        if node is None:
            # try in imports
            full_name = find_in_imports(self.root, name)

            class_ = self.module.package.visitor.manager.find_class(full_name)
            self.import_class_map[name] = class_

        else:
            class_ = self.class_visitor.visit(node)

        # TODO: try in assignments

        return class_

    def find_all_classes(self):
        # TODO: find by type
        pass

    def update_inheritance(self):
        return self.class_visitor.update_inheritance()


class PackageManager:
    # TODO: if not found, search installation?

    def __init__(self, packages_ls):
        self._packages_ls = packages_ls

        self._set_manager(packages_ls)

        self.Class = Class
        self._unknown_classes = {}

    def _set_manager(self, packages_ls):
        for package in packages_ls:
            package.visitor.manager = self

    @property
    def packages(self):
        return {package.name: package for package in self._packages_ls}

    def find_class(self, full_name):
        package_name = full_name.split('.')[0]
        package = self.packages.get(package_name, None)
        if package is None:

            class_ = self._unknown_classes.get(full_name,
                                               Class(full_name, None))
            self._unknown_classes[full_name] = class_
            return class_
        else:
            return package.visitor.find_class(full_name)

    def update_inheritance(self):
        while True:
            done = True
            for package in self._packages_ls:
                done_ = package.visitor.update_inheritance()
                if not done_:
                    done = False

            if done:
                break

    def get_classes(self):
        classes = {}
        for package in self._packages_ls:
            classes |= package.get_classes()

        classes |= self._unknown_classes

        return classes


class PackageVisitor:

    def __init__(self, package):
        self.package = package

        self.modules = []
        # TODO: inheritance method?

        self.all_modules_names = self._get_all_modules_names()

        self.Module = Module

        self.manager = self

    def find_class(self, full_name):
        full_name_ls = full_name.split('.')
        i = 0
        while True:
            i += 1

            if i > len(full_name_ls):
                # not an exception?
                raise Exception(f'Cannot find `{full_name}`')

            module_name = '.'.join(full_name_ls[:-i])
            if module_name in self.all_modules_names:
                # TODO: handle not finding
                class_name = '.'.join(full_name_ls[-i:])
                break

        module = self.package.modules.get(module_name, None)
        if module is None:
            module = self.Module(module_name, self.package)
            self.modules.append(module)

        return module.visitor.find_class(class_name)

    def find_all_classes(self):
        pass

    def _get_all_modules_names(self):
        paths = glob.glob(f'{self.package.path}/**/*.py', recursive=True)
        imports = [str(Path(path).relative_to(self.package.root_path)).split('.')[0].replace(os.path.sep, '.') for path in paths]

        # remove init
        imports = [import_[:-9] if import_.endswith('__init__') else import_ for import_ in imports]

        return set(imports)

    def update_inheritance(self):
        done = True
        for module in self.modules:
            done_ = module.visitor.update_inheritance()
            if not done_:
                done = False

        return done


class Package:

    def __init__(self, path):
        self.path = Path(path)

        self.visitor = PackageVisitor(self)

    @property
    def modules(self):
        return {module.full_name: module for module in self.visitor.modules}

    @property
    def name(self):
        return str(self.path).split(os.path.sep)[-1]

    @property
    def root_path(self):
        return self.path.parent

    def get_classes(self):
        classes = {}
        for module in self.modules.values():
            classes |= module.get_classes()

        return classes


class Module:

    def __init__(self, full_name, package):
        self.full_name = full_name
        self.package = package

        self.visitor = ModuleVisitor(self)

    @property
    def package_root(self):
        return self.package.root_path

    @property
    def path(self):
        return self.package_root / f"{self.full_name.replace('.', os.path.sep)}.py"

    @property
    def classes(self):
        return {class_.name: class_ for class_ in self.visitor.classes}

    def get_classes(self):
        return {class_.full_name: class_ for class_ in self.visitor.classes}


TmpBase = namedtuple('TmpBase', ['name', 'is_import'])


class Class:

    def __init__(self, name, module):
        self.module = module
        self.name = name
        self.attrs = []
        self.methods = []

        self.cls_attrs = []
        self._tmp_bases = []
        self.bases = []

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

    @property
    def full_name(self):
        return f'{self.module.full_name}.{self.name}'

    @property
    def short_name(self):
        return self.name.split('.')[-1]

    @property
    def id(self):
        return self.name.replace('.', '_')

    @property
    def found(self):
        return self.module is not None

    def __repr__(self):
        return f'<class: {self.short_name}>'

    def add_tmp_bases(self, bases):

        bases_ = []
        for node in bases:

            if isinstance(node, ast.Name):
                name = node.id
                is_import = False
            else:  # ast.Attribute
                name = f'{node.value.id}.{node.attr}'
                is_import = True

            bases_.append(TmpBase(name, is_import))

        self._tmp_bases.extend(bases_)

    def get_tmp_bases(self):
        return self._tmp_bases

    def reset_tmp_bases(self):
        self._tmp_bases = []

    def add_bases(self, bases):
        self.bases.extend(bases)

    def add_attr(self, node):
        # ast.Attribute
        self.attrs.append(node.attr)

    def add_local_vars(self, node):
        # ast.Name
        self.cls_attrs.append(node.id)

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
    def full_name(self):
        return f'{self.class_.module.full_name}.{self.name}'

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

    def add_local_vars(self, node):
        # ast.Name
        self.local_vars.append(node.id)

    def add_decorators(self, decorator_list):
        for node in decorator_list:
            # TODO: rethink due to function?
            if isinstance(node, ast.Name):
                name = node.id
            else:  # ast.Attribute
                name = f'{node.value.id}.{node.attr}'
            self.decorator_list.append(name)


class ClassVisitor(ast.NodeVisitor):

    def __init__(self, module):
        self.module = module

        self.classes = []
        self.stack = []

        self.Class = Class
        self.Method = Method

    @property
    def in_class(self):
        return isinstance(self.stack[-1], Class)

    @property
    def current_class(self):
        return self._get_last_from_stack(self.Class)

    @property
    def current_method(self):
        return self._get_last_from_stack(self.Method)

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

    def visit_Assign(self, node):
        current_class = self.current_class
        current_obj = self.current_obj

        for inner_node in node.targets:
            if isinstance(inner_node, ast.Attribute):
                current_class.add_attr(inner_node)
            else:  # ast.Name
                current_obj.add_local_vars(inner_node)

    def visit_ClassDef(self, node):
        class_ = self.Class(self._get_obj_name(node), self.module)

        class_.add_tmp_bases(node.bases)

        self.stack.append(class_)
        self.classes.append(class_)

        for inner_node in node.body:
            self.visit(inner_node)

        self.stack.pop()

        return class_

    def visit_FunctionDef(self, node):
        func = self.Method(self._get_obj_name(node), self.current_class)
        func.add_decorators(node.decorator_list)

        self.stack.append(func)

        for inner_node in node.body:
            self.visit(inner_node)

        self.stack.pop()

    def _get_obj_name(self, node):
        name = node.name
        prefix = self._get_prefix_from_stack()
        if prefix:
            name = f'{prefix}.{name}'

        return name

    def update_inheritance(self):
        done = True
        for class_ in self.classes:
            # TODO: add not found class?
            bases = []
            for tmp_base in class_.get_tmp_bases():
                done = False
                if tmp_base.is_import:
                    base = self.module.package.visitor.manager.find_class(tmp_base.name)
                else:
                    base = self.module.visitor.find_class(tmp_base.name)

                bases.append(base)

            class_.add_bases(bases)
            class_.reset_tmp_bases()

        return done
