
import graphviz

from calatrava.filters import apply_filters


def _get_block_str(block, symbol=''):
    if block:
        return symbol + fr'\l{symbol}'.join(block) + r'\l'
    return ''


class RecordCreator:

    def __init__(self, class_attr_name='name', show_cls_attrs=False,
                 sep_props=False, styles=None):
        self.class_attr_name = class_attr_name
        self.show_cls_attrs = show_cls_attrs
        self.sep_props = sep_props

        self.styles = {} if styles is None else styles

        self._default_styles = {
            'normal': {'shape': 'record', 'color': 'black'},
            'abstract': {'shape': 'record', 'color': 'blue'},
            'not_found': {'shape': 'oval', 'color': 'red'},
        }
        self._update_styles()

    def _update_styles(self):
        self.styles.update(self._default_styles)
        for key, value in self._default_styles.items():
            self.styles[key].update(value)

    def _get_node_name(self, class_):
        return getattr(class_, self.class_attr_name)

    def create_node(self, dot, class_):
        if class_.found:
            style = self.styles.get('abstract') if class_.is_abstract else self.styles.get('normal')
            label = self._get_node_label(class_)
            dot.node(class_.id, label=label, **style)
        else:
            style = self.styles.get('not_found')
            dot.node(class_.id, label=self._get_node_name(class_),
                     **style)

    def _get_node_label(self, class_):
        attrs_str = self._get_attrs_str(class_)
        methods_str = self._get_methods_str(class_)

        node_name = self._get_node_name(class_)

        return '{' + f"{node_name}|{attrs_str}|{methods_str}" + '}'

    def _get_attrs_str(self, class_):
        attrs_str = ''
        if self.show_cls_attrs:
            cls_attrs = class_.cls_attrs
            attrs_str += f"{_get_block_str(sorted(cls_attrs), symbol='+')}|"

        attrs = set(class_.attrs)
        base_attrs = set(class_.base_attrs).difference(attrs)

        attrs_str += _get_block_str(sorted(attrs), symbol='+')
        attrs_str += _get_block_str(sorted(base_attrs), symbol='-')

        return attrs_str

    def _get_methods_str(self, class_):
        methods_str = ''
        if self.sep_props:
            props = [method for method in class_.methods if method.is_property]
            base_props = [method for method in class_.base_methods if method.is_property]

            props_names = set(self._get_method_names(props, suffix=''))
            base_props_names = set(self._get_method_names(base_props, suffix='')).difference(props_names)

            methods_str += _get_block_str(sorted(props_names), symbol='+')
            methods_str += f"{_get_block_str(sorted(base_props_names), symbol='-')}|"

            methods = [method for method in class_.methods if not method.is_property]
            base_methods = [method for method in class_.base_methods if not method.is_property]

        else:
            methods = class_.methods
            base_methods = class_.base_methods

        methods_names = set(self._get_method_names(methods))
        base_methods_names = set(self._get_method_names(base_methods)).difference(methods_names)

        methods_str += _get_block_str(sorted(methods_names), symbol='+')
        methods_str += _get_block_str(sorted(base_methods_names), symbol='-')

        return methods_str

    def _get_method_names(self, methods, suffix='()'):
        return [f'{method.short_name}{suffix}' for method in methods]


def create_graph(classes, record_creator=None, filters=()):
    if record_creator is None:
        record_creator = RecordCreator()

    filtered_classes = apply_filters(filters, classes)

    dot = graphviz.Digraph()

    for class_ in filtered_classes:
        record_creator.create_node(dot, class_)

    for class_ in filtered_classes:
        for base_class in class_.bases:
            if base_class not in filtered_classes:
                continue

            dot.edge(base_class.id, class_.id, dir='back', arrowtail='empty')

    return dot


def save_graph(dot, filename, view=True, format='svg', **kwargs):
    dot.render(filename, view=view, format=format, **kwargs)
