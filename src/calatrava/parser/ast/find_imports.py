
import ast

from calatrava.parser.ast.base import (
    BaseModule,
    BaseModuleMixins,
    BasePackage,
    BasePackageMixins,
    BasePackageManager,
    BasePackageManagerMixins,
)
from calatrava.parser.ast.node_visitors import (
    get_import_from_module_name,
)


class ImportsVisitor(ast.NodeVisitor):

    def __init__(self, module):
        self.module = module

    def visit_Import(self, node):
        self.module.imports.extend([node.name for node in node.names])

    def visit_ImportFrom(self, node):
        node_module = get_import_from_module_name(
            node, self.module.long_name, self.module.is_init)

        self.module.imports.extend(
            [f"{node_module}.{name.name}" for name in node.names]
        )


class ModuleMixins(BaseModuleMixins):

    def __init__(self, ImportsVisitor, **kwargs):
        super().__init__(**kwargs)
        self.imports_visitor = ImportsVisitor(self)
        self.imports = []

    def get_imports(self):
        if len(self.imports) == 0:
            self.imports_visitor.visit(self.root)

        return self.imports

    @property
    def internal_imports(self):
        package_name = self.package.name
        return [name for name in self.imports if name.split('.')[0] == package_name]

    @property
    def external_imports(self):
        package_name = self.package.name
        return [name for name in self.imports if name.split('.')[0] != package_name]

    @property
    def has_imports(self):
        return len(self.imports) > 0

    @property
    def has_internal_imports(self):
        return len(self.internal_imports) > 0

    @property
    def has_star_imports(self):
        for name in self.imports:
            if name.split('.')[-1] == "*":
                return True

        return False

    def get_module_level_internal_imports(self, modules_names):
        imports = []
        for import_ in self.internal_imports:
            import_initial = import_
            while True:
                if import_ in modules_names:
                    imports.append(import_)
                    break

                import_ = '.'.join(import_.split(".")[:-1])
                if import_ == "":
                    raise Exception(f"Cannot handle `{import_initial}`.")

        return imports

    def get_simplified_external_imports(self):
        return [import_.split('.') for import_ in self.external_imports]


class Module(ModuleMixins, BaseModule):
    # TODO: pass ImportsVisitor in package instead

    def __init__(self, long_name, package, ImportsVisitor=ImportsVisitor):
        super().__init__(long_name=long_name, package=package,
                         ImportsVisitor=ImportsVisitor)


class PackageMixins(BasePackageMixins):

    def get_imports(self):
        imports = []
        for module in self.modules_ls:
            imports.extend(module.get_imports())

        return imports


class Package(PackageMixins, BasePackage):

    def __init__(self, path, Module=Module):
        super().__init__(path=path, Module=Module)


class PackageManagerMixins(BasePackageManagerMixins):
    def get_imports(self):
        imports = []
        for package in self.packages_ls:
            imports.extend(package.get_imports())

        return imports


class PackageManager(PackageManagerMixins, BasePackageManager):
    pass
