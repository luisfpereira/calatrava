
import ast
from pathlib import Path
import os
import tokenize
import glob
from collections import namedtuple
import pkgutil
import logging

logging.basicConfig(format='%(message)s', level=logging.INFO)


PYTHON_PROTECTED_CLASSES = (
    'Exception', 'type', 'object', 'dict', 'list', 'tuple', 'set',
)


def find_by_name(root, type_, name):
    for node in ast.walk(root):
        if isinstance(node, type_) and node.name == name:
            return node


def _get_import_from_module_name(node, module_name, module_is_init=False):
    # ast.ImportFrom
    if node.level:  # handle local imports
        level = -(node.level - 1) if module_is_init else -node.level
        if level == 0:
            level = None
        node_module = '.'.join(module_name.split('.')[:level])
        if node.module:
            node_module += f'.{node.module}'
    else:
        node_module = node.module

    return node_module


def find_in_imports(root, search_name, module_name, module_is_init=False):
    for node in ast.walk(root):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        for name in node.names:
            if search_name == name.name or search_name == name.asname:
                if isinstance(node, ast.Import):
                    return name.name
                else:  # ast.ImportFrom
                    node_module = _get_import_from_module_name(
                        node, module_name, module_is_init)

                    return f'{node_module}.{name.name}'


def collect_star_imports(root, module_name, module_is_init):
    star_imports = []
    for node in ast.walk(root):
        if not isinstance(node, ast.ImportFrom):
            continue

        if node.names[0].name == '*':
            module_name = _get_import_from_module_name(
                node, module_name, module_is_init)
            star_imports.append(module_name)

    return star_imports


class _AttributeVisitor(ast.NodeVisitor):

    def __init__(self):
        self._full_name_ls = []

    def collect_full_name(self, node):
        self._full_name_ls = []

        self.visit(node)

        return '.'.join(reversed(self._full_name_ls))

    def visit_Attribute(self, node):
        self._full_name_ls.append(node.attr)
        self.visit(node.value)

    def visit_Name(self, node):
        self._full_name_ls.append(node.id)


_attribute_visitor = _AttributeVisitor()


def collect_attr_full_name(node):
    # ast.Attribute
    return _attribute_visitor.collect_full_name(node)


class _AssignVisitor(ast.NodeVisitor):

    def __init__(self):
        self._target_names = []

    def collect_targets(self, node):
        self._target_names = []

        for node_ in node.targets:
            self.visit(node_)

        return self._target_names

    def visit_Name(self, node):
        self._target_names.append(node.id)

    def visit_Tuple(self, node):
        for node_ in node.dims:
            self.visit(node_)

    def visit_Attribute(self, node):
        self._target_names.append(collect_attr_full_name(node))


_assign_visitor = _AssignVisitor()


def collect_assign_targets(node):
    # ast.Assign
    return _assign_visitor.collect_targets(node)


class ModuleVisitor:

    def __init__(self, module):
        self.module = module
        self.class_visitor = ClassVisitor(module)

        self.root = self._load_root()

        self.import_class_map = {}
        self.not_found = {}
        self.not_found_trial = {}

    @property
    def classes(self):
        return self.class_visitor.classes

    def _load_root(self):
        with tokenize.open(self.module.path) as file:
            root = ast.parse(file.read(), self.module.path)

        return root

    def find_class(self, name, visited=()):
        # visited only for possible recursion due to star imports
        if self.module in visited:
            return

        # TODO: merge
        # try in existing
        class_ = self.module.classes.get(name, None)
        if class_ is not None:
            return class_

        # try in import map
        class_ = self.import_class_map.get(name, None)
        if class_ is not None:
            return class_

        # try in not found map
        class_ = self.not_found.get(name, None)
        if class_ is not None:
            return class_

        # try in not found trial
        class_ = self.not_found_trial.get(name, None)
        if class_ is not None:
            return class_

        # try in python protected names
        if name in PYTHON_PROTECTED_CLASSES:
            return self.module.package.visitor.manager.find_class(name)

        # try in definitions
        node = find_by_name(self.root, ast.ClassDef, name)
        if node is not None:
            return self.class_visitor.visit(node)

        # try in imports
        full_name = find_in_imports(
            self.root, name, self.module.full_name, self.module.is_init)
        if full_name is not None:
            class_ = self.module.package.visitor.manager.find_class(full_name)
            self.import_class_map[name] = class_
            return class_

        # try in start imports
        star_imports = collect_star_imports(self.root, self.module.full_name,
                                            self.module.is_init)
        if star_imports:
            if visited:
                visited.append(self.module)
            else:
                visited = [self.module]

            for star_import in star_imports:
                full_name = f'{star_import}.{name}'
                class_ = self.module.package.visitor.manager.find_class(
                    full_name, visited=visited)
                if class_ is not None:
                    self.import_class_map[name] = class_
                    return class_

        if not visited:
            # not found (e.g. assignment)
            class_ = self.class_visitor.Class(name, self.module,
                                              found=False)
            self.module.package.visitor.manager.add_unknown_class(class_)
            self.not_found[name] = class_

            return class_

    def find_all_classes(self):
        class_nodes = [node for node in self.root.body if isinstance(node, ast.ClassDef)]
        return [self.class_visitor.visit(node) for node in class_nodes]

    def update_inheritance(self):
        return self.class_visitor.update_inheritance()


class PackageManager:

    def __init__(self, packages_ls):
        self._packages_ls = packages_ls

        self._set_manager(packages_ls)

        self.Class = Class
        self._unknown_classes = {}

    def _set_manager(self, packages_ls):
        for package in packages_ls:
            package.visitor.manager = self

    def _get_package(self, full_name, raise_=False):
        package_name = full_name.split('.')[0]
        package = self.packages.get(package_name, None)

        if raise_ and package is None:
            raise Exception(f"Cannot find package `{package_name}`")

        return package

    def add_unknown_class(self, class_):
        self._unknown_classes[class_.full_name] = class_

    @ property
    def packages(self):
        return {package.name: package for package in self._packages_ls}

    def find_class(self, full_name, visited=()):
        package = self._get_package(full_name)
        if package is None and visited:
            return
        elif package is None:
            class_ = self._unknown_classes.get(full_name,
                                               self.Class(full_name, None))
            self.add_unknown_class(class_)
            return class_
        else:
            return package.visitor.find_class(full_name, visited=visited)

    def find_module(self, full_name):
        package = self._get_package(full_name, raise_=True)

        return package.visitor.find_module(full_name)

    def find_subpackage(self, full_name):
        package = self._get_package(full_name)
        return package.visitor.find_subpackage(full_name)

    def find_all(self):
        classes = []
        for package in self._packages_ls:
            classes.extend(package.visitor.find_all())

        return classes

    def find(self, import_):
        package = self._get_package(import_, raise_=True)
        return package.visitor.find(import_)

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

        self.all_modules_names = self._get_all_modules_names()
        self.all_subpackages_names = self._get_all_subpackages_names()

        self.Module = Module
        self.manager = self  # to work in basic case

    def _get_module(self, full_name):
        module = self.package.modules.get(full_name, None)
        if module is None:
            module = self.Module(full_name, self.package)
            self.modules.append(module)

        return module

    def find_class(self, full_name, visited=()):
        full_name_ls = full_name.split('.')
        i = 0
        while True:
            i += 1

            if i > len(full_name_ls):
                raise Exception(f'Cannot find `{full_name}`')

            module_name = '.'.join(full_name_ls[:-i])
            if module_name in self.all_modules_names:
                class_name = '.'.join(full_name_ls[-i:])
                break

        module = self._get_module(module_name)
        return module.visitor.find_class(class_name, visited=visited)

    def find_module(self, full_name):
        module = self._get_module(full_name)

        return module.visitor.find_all_classes()

    def _find_modules(self, module_names):
        all_classes = []
        for module_name in module_names:
            all_classes.extend(self.find_module(module_name))

        return all_classes

    def find_subpackage(self, full_name):
        module_names = [module_name for module_name in self.all_modules_names if module_name.startswith(full_name)]
        return self._find_modules(module_names)

    def find_all(self):
        return self._find_modules(self.all_modules_names)

    def find(self, import_):
        if import_ in self.all_subpackages_names:
            return self.find_subpackage(import_)
        elif import_ in self.all_modules_names:
            return self.find_module(import_)

        return self.find_class(import_)

    def _get_all_modules_names(self):
        sep = os.path.sep
        paths = glob.glob(f'{self.package.path}{sep}**{sep}*.py', recursive=True)
        imports = [str(Path(path).relative_to(self.package.root_path)).split('.')[0].replace(os.path.sep, '.') for path in paths]

        # remove init
        imports = [import_[:-9] if import_.endswith('__init__') else import_ for import_ in imports]

        return set(imports)

    def _get_all_subpackages_names(self):
        sep = os.path.sep
        paths = [path for path in glob.glob(f'{self.package.path}{sep}*{sep}', recursive=True) if not path.endswith('__pycache__/')]
        imports = [str(Path(path).relative_to(self.package.root_path)).split('.')[0].replace(os.path.sep, '.') for path in paths]

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

        path_exists = os.path.exists(path)
        if not path_exists or (path_exists and not os.path.isdir(path)):
            # FIXME: will fail in tons of cases
            package_name = path
            package = pkgutil.get_loader(package_name)

            path = f'{os.path.sep}'.join(package.path.split(os.path.sep)[:-1])
            logging.info(f"Found `{package_name}` in `{path}`")

        self.path = Path(path)

        self.visitor = PackageVisitor(self)

    @ property
    def modules(self):
        return {module.full_name: module for module in self.visitor.modules}

    @ property
    def name(self):
        return str(self.path).split(os.path.sep)[-1]

    @ property
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

    @ property
    def is_init(self):
        return os.path.exists(self._get_init_path())

    @ property
    def package_root(self):
        return self.package.root_path

    def _get_path_beginning(self):
        return self.package_root / f"{self.full_name.replace('.', os.path.sep)}"

    def _get_init_path(self, path_beginning=None):
        path_beginning = path_beginning or self._get_path_beginning()
        return f"{path_beginning}{os.path.sep}__init__.py"

    @ property
    def path(self):
        name = self._get_path_beginning()
        path = f"{name}.py"

        return path if os.path.exists(path) else self._get_init_path(name)

    @ property
    def classes(self):
        return {class_.name: class_ for class_ in self.visitor.classes}

    def get_classes(self):
        return {class_.full_name: class_ for class_ in self.visitor.classes}


TmpBase = namedtuple('TmpBase', ['name', 'is_import'])


class Class:

    def __init__(self, name, module, found=True):
        self.module = module
        self.name = name
        self.attrs = []
        self.methods = []

        self.cls_attrs = []
        self._tmp_bases = []
        self.bases = []

        self.children = []
        self._found = found

    def __repr__(self):
        return f'<class: {self.full_name}>'

    @ property
    def all_attrs(self):
        return self.attrs + self.base_attrs

    @ property
    def base_attrs(self):
        attrs = []
        for base in self.bases:
            attrs.extend(base.all_attrs)

        return attrs

    @ property
    def all_methods(self):
        return self.methods + self.base_methods

    @ property
    def base_methods(self):
        methods = []
        for base in self.bases:
            methods.extend(base.all_methods)
        return methods

    @ property
    def full_name(self):
        if self.module:
            return f'{self.module.full_name}.{self.name}'
        else:
            return self.name

    @ property
    def short_name(self):
        return self.name.split('.')[-1]

    @ property
    def id(self):
        return self.full_name.replace('.', '_')

    @ property
    def found(self):
        return self.module is not None and self._found

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
                name = collect_attr_full_name(node)
                is_import = True

            bases.append(TmpBase(name, is_import))

        self._tmp_bases.extend(bases)

    def get_tmp_bases(self):
        return self._tmp_bases

    def reset_tmp_bases(self):
        self._tmp_bases = []

    def add_base(self, base):
        self.bases.append(base)
        base.add_child(self)

    def add_attr(self, attr_name):
        self.attrs.append(attr_name)

    def add_local_var(self, var_name):
        self.cls_attrs.append(var_name)

    def add_method(self, method):
        self.methods.append(method)

    def add_child(self, child):
        self.children.append(child)


class Method:

    def __init__(self, name, class_):
        self.class_ = class_
        class_.add_method(self)

        self.name = name
        self.local_vars = []
        self.decorator_list = []

    @ property
    def full_name(self):
        return f'{self.class_.module.full_name}.{self.name}'

    @ property
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

    @ property
    def is_property(self):
        return 'property' in self.decorator_list

    @ property
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
                name = collect_attr_full_name(node)
            self.decorator_list.append(name)


class ClassVisitor(ast.NodeVisitor):

    def __init__(self, module):
        self.module = module

        self.classes = []
        self.stack = []

        self.Class = Class
        self.Method = Method

    @ property
    def in_class(self):
        return isinstance(self.stack[-1], Class)

    @ property
    def current_class(self):
        return self._get_last_from_stack(self.Class)

    @ property
    def current_method(self):
        return self._get_last_from_stack(self.Method)

    @ property
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

        target_names = collect_assign_targets(node)

        for target_name in target_names:
            target_name_ls = target_name.split('.')
            if len(target_name_ls) == 2 and target_name_ls[0] == 'self':
                current_class.add_attr(target_name_ls[1])
            elif len(target_name_ls) == 1:
                current_obj.add_local_var(target_name)

    def visit_ClassDef(self, node):
        class_ = self.Class(self._get_obj_name(node), self.module)

        class_.add_tmp_bases(node)

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
            for tmp_base in class_.get_tmp_bases():
                done = False
                if tmp_base.is_import:
                    base = self.module.package.visitor.manager.find_class(tmp_base.name)
                else:
                    base = self.module.visitor.find_class(tmp_base.name)

                class_.add_base(base)

            class_.reset_tmp_bases()

        return done
