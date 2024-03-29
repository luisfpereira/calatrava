
from abc import ABCMeta
import os
import ast
import pkgutil
import logging
import glob
from pathlib import Path
import tokenize


class BasePackageManager:

    def __init__(self, packages_ls):
        self.packages_ls = packages_ls

        self._set_manager(packages_ls)

    def _set_manager(self, packages_ls):
        for package in packages_ls:
            package.manager = self

    def _get_package(self, long_name, raise_=False):
        package_name = long_name.split('.')[0]
        package = self.packages.get(package_name, None)

        if raise_ and package is None:
            raise Exception(f"Cannot find package `{package_name}`")

        return package

    @property
    def packages(self):
        return {package.name: package for package in self.packages_ls}

    @property
    def modules(self):
        modules = {}
        for package in self.packages_ls:
            modules |= package.modules
        return modules

    def find_module(self, long_name):
        package = self._get_package(long_name, raise_=True)

        return package.find_module(long_name)

    def find_modules(self):
        # TODO: find all modules instead?
        modules = []
        for package in self.packages_ls:
            modules.extend(package.find_modules())

        return modules


class BasePackageManagerMixins(metaclass=ABCMeta):
    pass


class BasePackage:

    def __init__(self, path, Module):

        path_exists = os.path.exists(path)
        if not path_exists or (path_exists and not os.path.isdir(path)):
            # FIXME: will fail in tons of cases
            package_name = path
            package = pkgutil.get_loader(package_name)

            path = f'{os.path.sep}'.join(package.path.split(os.path.sep)[:-1])
            logging.info(f"Found `{package_name}` in `{path}`")

        self.path = Path(path)
        self.modules_ls = []

        self.modules_names = self._get_modules_names()
        self.extra_modules_names = self._get_extra_modules_names()
        self.subpackages_names = self._get_subpackages_names()

        self.manager = self  # to work in basic case

        self.Module = Module

    @property
    def modules(self):
        return {module.long_name: module for module in self.modules_ls}

    @property
    def name(self):
        return str(self.path).split(os.path.sep)[-1]

    @property
    def root_path(self):
        return self.path.parent

    def _get_modules_names(self):
        sep = os.path.sep
        paths = glob.glob(f'{self.path}{sep}**{sep}*.py', recursive=True)
        imports = [str(Path(path).relative_to(self.root_path)).split('.')[0].replace(os.path.sep, '.') for path in paths]

        # remove init
        imports = [import_[:-9] if import_.endswith('__init__') else import_ for import_ in imports]

        return set(imports)

    def _get_extra_modules_names(self):
        sep = os.path.sep
        paths = []
        for ext in ["pyi", "pyi.in", "pyx", "pyc"]:
            paths.extend(glob.glob(f'{self.path}{sep}**{sep}*.{ext}', recursive=True))
        imports = [str(Path(path).relative_to(self.root_path)).split('.')[0].replace(os.path.sep, '.') for path in paths]

        # remove init
        imports = [import_[:-9] if import_.endswith('__init__') else import_ for import_ in imports]

        return set(imports)

    def _get_subpackages_names(self):
        sep = os.path.sep
        paths = [path for path in glob.glob(f'{self.path}{sep}*{sep}', recursive=True) if not path.endswith('__pycache__/')]
        imports = [str(Path(path).relative_to(self.root_path)).split('.')[0].replace(os.path.sep, '.') for path in paths]

        return set(imports)

    def find_module(self, long_name):
        module = self.modules.get(long_name, None)
        if module is None and long_name in self.modules_names:
            module = self.Module(long_name, self)
            self.modules_ls.append(module)

        return module

    def find_modules(self):
        modules = self.modules
        for module_name in self.modules_names:
            if module_name in modules:
                continue

            self.find_module(module_name)

        return self.modules_ls


class BasePackageMixins(metaclass=ABCMeta):
    pass


class BaseModule:

    def __init__(self, long_name, package):
        self.long_name = long_name
        self.package = package

        self.root = self._load_root()

    @property
    def id(self):
        return self.long_name.replace('.', '_')

    @property
    def is_init(self):
        return os.path.exists(self._get_init_path())

    @property
    def package_root(self):
        return self.package.root_path

    def _get_path_beginning(self):
        return self.package_root / f"{self.long_name.replace('.', os.path.sep)}"

    def _get_init_path(self, path_beginning=None):
        path_beginning = path_beginning or self._get_path_beginning()
        return f"{path_beginning}{os.path.sep}__init__.py"

    def _load_root(self):
        with tokenize.open(self.path) as file:
            root = ast.parse(file.read(), self.path)

        return root

    @property
    def path(self):
        name = self._get_path_beginning()
        path = f"{name}.py"

        return path if os.path.exists(path) else self._get_init_path(name)


class BaseModuleMixins(metaclass=ABCMeta):
    pass
