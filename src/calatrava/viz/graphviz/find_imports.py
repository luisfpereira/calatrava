
import graphviz

from calatrava.viz.graphviz.base import BaseRecordCreator


def _get_id(name):
    return name.replace(".", "_")


class GenericRecordCreator(BaseRecordCreator):
    def __init__(self, shape="record", color="black"):
        styles = {"normal": {"shape": shape, "color": color}}
        super().__init__(default_styles={}, styles=styles)

    def create_node(self, dot, id_, name):
        dot.node(id_, label=name, **self.styles["normal"])


class ModuleRecordCreator(BaseRecordCreator):

    def __init__(self, shape="record", color="black"):
        styles = {"normal": {"shape": shape, "color": color}}
        super().__init__(default_styles={}, styles=styles)

    def create_node(self, dot, module):
        dot.node(module.id, label=module.long_name, **self.styles["normal"])


def create_graph(package_manager, exclude=(), add_to_modules_names=None):
    # TODO
    # for now is very particular

    if add_to_modules_names is None:
        add_to_modules_names = {}

    # collect imports and modules
    all_internal_imports = []
    for package in package_manager.packages_ls:
        modules_names = package.modules_names | set(add_to_modules_names.get(package.name, []))
        for module in package.modules_ls:
            all_internal_imports.extend(
                module.get_module_level_internal_imports(modules_names)
            )

    all_internal_imports = set(all_internal_imports) - set(exclude)
    all_parsed_modules = package_manager.modules
    for exclude_import in exclude:
        if exclude_import in all_parsed_modules:
            del all_parsed_modules[exclude_import]

    dot = graphviz.Digraph()

    # draw nodes
    module_record_creator = ModuleRecordCreator(color="blue")
    record_creator = GenericRecordCreator(shape="oval")

    for module in all_parsed_modules.values():
        # TODO: if depends on representation of external nodes
        if module.has_internal_imports or module.long_name in all_internal_imports:
            module_record_creator.create_node(dot, module)

    for internal_import in all_internal_imports:
        if internal_import in all_parsed_modules:
            continue

        record_creator.create_node(
            dot, _get_id(internal_import), internal_import)

    # draw edges
    for module in all_parsed_modules.values():
        for internal_import in set(module.get_module_level_internal_imports(modules_names)):
            if internal_import not in all_internal_imports:
                continue

            dot.edge(module.id, _get_id(internal_import))

    return dot
