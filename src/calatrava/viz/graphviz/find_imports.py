
import graphviz


def _get_id(name):
    return name.replace(".", "_")


class RecordCreator:

    def __init__(self, shape="record", color="black"):
        self.style = {"shape": shape, "color": color}

    def create_node(self, dot, id_, name):
        dot.node(id_, label=name, **self.style)


class ModuleRecordCreator(RecordCreator):

    def create_node(self, dot, module):
        dot.node(module.id, label=module.long_name, **self.style)


def create_graph(package_manager):
    # TODO
    # for now is very particular

    # collect imports and modules
    all_internal_imports = []
    for package in package_manager.packages_ls:
        modules_names = package.modules_names
        for module in package.modules_ls:
            all_internal_imports.extend(
                module.get_module_level_internal_imports(modules_names)
            )

    all_internal_imports = set(all_internal_imports)
    all_parsed_modules = package_manager.modules

    dot = graphviz.Digraph()

    # draw nodes
    module_record_creator = ModuleRecordCreator(color="blue")
    record_creator = RecordCreator(shape="oval")

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
