

import ast


def find_by_name(root, type_, name):
    for node in ast.walk(root):
        if isinstance(node, type_) and node.name == name:
            return node


def get_import_from_module_name(node, module_name, module_is_init=False):
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
                    node_module = get_import_from_module_name(
                        node, module_name, module_is_init)

                    return f'{node_module}.{name.name}'


def collect_star_imports(root, module_name, module_is_init):
    star_imports = []
    for node in ast.walk(root):
        if not isinstance(node, ast.ImportFrom):
            continue

        if node.names[0].name == '*':
            module_name = get_import_from_module_name(
                node, module_name, module_is_init)
            star_imports.append(module_name)

    return star_imports


class AttributeVisitor(ast.NodeVisitor):

    def __init__(self):
        self._long_name_ls = []

    def collect_long_name(self, node):
        self._long_name_ls = []

        self.visit(node)

        return '.'.join(reversed(self._long_name_ls))

    def visit_Attribute(self, node):
        self._long_name_ls.append(node.attr)
        self.visit(node.value)

    def visit_Name(self, node):
        self._long_name_ls.append(node.id)


class AssignVisitor(ast.NodeVisitor):

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
        self._target_names.append(collect_attr_long_name(node))


_attribute_visitor = AttributeVisitor()


def collect_attr_long_name(node):
    # ast.Attribute
    return _attribute_visitor.collect_long_name(node)


_assign_visitor = AssignVisitor()


def collect_assign_targets(node):
    # ast.Assign
    return _assign_visitor.collect_targets(node)
