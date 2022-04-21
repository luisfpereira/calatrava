
import graphviz


def _get_method_names(cls):
    return [f"{method.name.split('.')[-1]}()" for method in cls.methods]


def _get_block_str(block, symbol=''):
    if len(block) == 0:
        return ''
    return symbol + fr'\l{symbol}'.join(block) + r'\l'


def _get_node_label(cls, base_attrs, base_methods):
    attrs = sorted(list(set(cls.attrs)))
    base_attrs = sorted(list(set([attr for attr in base_attrs if attr not in attrs])))

    attrs_str = _get_block_str(attrs, symbol='+')
    attrs_str += _get_block_str(base_attrs, symbol='-')

    method_names = sorted(list(set(_get_method_names(cls))))
    base_methods = sorted(list(set([method for method in base_methods if method not in method_names])))

    methods_str = _get_block_str(method_names, symbol='+')
    methods_str += _get_block_str(base_methods, symbol='-')

    node_name = cls.name.split('.')[-1]

    return '{' + f"{node_name}|{attrs_str}|{methods_str}" + '}'


def _add_inheritance(dot, cls_name, existing_classes,
                     existing_nodes, existing_edges, not_found):
    cls = existing_classes[cls_name]

    base_attrs, base_methods = [], []
    for base_cls_name in cls.base_classes:
        if base_cls_name not in existing_classes:
            not_found.append(base_cls_name)
            continue

        base_attrs_, base_methods_ = _add_inheritance(
            dot, base_cls_name, existing_classes, existing_nodes, existing_edges, not_found)

        edge_name = f'{base_cls_name}->{cls_name}'

        if edge_name not in existing_edges:
            dot.edge(base_cls_name, cls_name,
                     dir='back', arrowtail='empty')

        base_attrs.extend(base_attrs_)
        base_methods.extend(base_methods_)

        existing_edges.append(edge_name)

    if cls_name not in existing_nodes:
        node_label = _get_node_label(cls, base_attrs, base_methods)
        dot.node(cls.name, label=node_label, shape='record')

    attrs = list(set(cls.attrs + base_attrs))
    methods = list(set(_get_method_names(cls) + base_methods))

    existing_nodes.append(cls_name)

    return attrs, methods


def create_graph(existing_classes, main_cls_names=(),
                 filtered_cls_names=()):
    main_cls_names = main_cls_names or list(existing_classes.keys())

    existing_nodes = []
    existing_edges = []
    not_found = []

    dot = graphviz.Digraph()

    for main_cls_name in set(main_cls_names).difference(filtered_cls_names):
        _add_inheritance(dot, main_cls_name, existing_classes,
                         existing_nodes, existing_edges, not_found)

    return dot


def save_graph(dot, filename, view=True, format='svg', **kwargs):
    dot.render(filename, view=view, format=format, **kwargs)
