
import graphviz


def _get_block_str(block, symbol=''):
    if len(block) == 0:
        return ''
    return symbol + fr'\l{symbol}'.join(block) + r'\l'


class RecordCreator:

    def create_node(self, dot, class_):
        if class_.found:
            label = self.get_node_label(class_)
            dot.node(class_.id, label=label, shape='record')
        else:
            dot.node(class_.id, label=class_.name)

    def get_node_label(self, class_):
        # TODO: add class methods and properties
        attrs_str = self._get_attrs_str(class_)
        methods_str = self._get_methods_str(class_)

        node_name = class_.name

        return '{' + f"{node_name}|{attrs_str}|{methods_str}" + '}'

    def _get_attrs_str(self, class_):
        attrs = set(class_.attrs)
        base_attrs = set(class_.base_attrs).difference(attrs)

        attrs_str = _get_block_str(sorted(attrs), symbol='+')
        attrs_str += _get_block_str(sorted(base_attrs), symbol='-')

        return attrs_str

    def _get_methods_str(self, class_):
        methods = set(self._get_method_names(class_.methods))
        base_methods = set(self._get_method_names(class_.base_methods)).difference(methods)

        methods_str = _get_block_str(sorted(methods), symbol='+')
        methods_str += _get_block_str(sorted(base_methods), symbol='-')

        return methods_str

    def _get_method_names(self, methods):
        return [f'{method.short_name}()' for method in methods]


def create_graph(classes, record_creator=None):
    if record_creator is None:
        record_creator = RecordCreator()

    dot = graphviz.Digraph()

    for class_ in classes:
        record_creator.create_node(dot, class_)

    for class_ in classes:
        for base_class in class_.bases:
            dot.edge(base_class.id, class_.id, dir='back', arrowtail='empty')

    return dot


def save_graph(dot, filename, view=True, format='svg', **kwargs):
    dot.render(filename, view=view, format=format, **kwargs)
