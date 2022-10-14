
import graphviz

from calatrava.post_filters.uml import apply_filters
from calatrava.utils import import_class_from_str
from calatrava.viz.graphviz.base import BaseRecordCreator


def _get_block_str(block, symbol='', keep_private=True):
    if not keep_private:
        block = [elem for elem in block if not elem.startswith('_')]

    if block:
        return symbol + fr'\l{symbol}'.join(block) + r'\l'
    return ''


def load_record_creator_from_dict(metadata):
    type_ = metadata.get('type', 'DEFAULT_RECORD_CREATOR')
    RecordCreator_ = import_class_from_str(type_) if '.' in type_ else globals().get(type_)

    kwargs = metadata.copy()
    kwargs.pop('type', None)

    return RecordCreator_(**kwargs)


class RecordCreator(BaseRecordCreator):

    def __init__(self, class_attr_name='name',
                 show_attrs=True, show_cls_attrs=False,
                 show_methods=True, separate_props=False,
                 styles=None, keep_private=True):

        default_styles = {
            'normal': {'shape': 'record', 'color': 'black'},
            'abstract': {'shape': 'record', 'color': 'blue'},
            'not_found': {'shape': 'oval', 'color': 'red'},
        }

        super().__init__(default_styles=default_styles, styles=styles)

        self.class_attr_name = class_attr_name
        self.show_attrs = show_attrs
        self.show_cls_attrs = show_cls_attrs
        self.show_methods = show_methods
        self.separate_props = separate_props
        self.keep_private = keep_private

    def create_node(self, dot, class_):
        if class_.found:
            style = self.styles.get('abstract') if class_.is_abstract else self.styles.get('normal')
            label = self._get_node_label(class_)
            dot.node(class_.id, label=label, **style)
        else:
            style = self.styles.get('not_found')
            dot.node(class_.id, label=self._get_node_name(class_),
                     **style)

    def _get_node_name(self, class_):
        return getattr(class_, self.class_attr_name)

    def _get_node_label(self, class_):
        node_name = self._get_node_name(class_)

        label = '{' + f"{node_name}"

        if self.show_attrs:
            attrs_str = self._get_attrs_str(class_)
            label += f"|{attrs_str}"

        if self.show_methods:
            methods_str = self._get_methods_str(class_)
            label += f"|{methods_str}"

        label += '}'
        return label

    def _get_attrs_str(self, class_):
        attrs_str = ''
        if self.show_cls_attrs:
            cls_attrs = class_.cls_attrs
            attrs_str += f"{_get_block_str(sorted(cls_attrs), symbol='+', keep_private=self.keep_private)}|"

        attrs = set(class_.attrs)
        base_attrs = set(class_.base_attrs).difference(attrs)

        attrs_str += _get_block_str(sorted(attrs), symbol='+', keep_private=self.keep_private)
        attrs_str += _get_block_str(sorted(base_attrs), symbol='-', keep_private=self.keep_private)

        return attrs_str

    def _get_methods_str(self, class_):
        methods_str = ''
        if self.separate_props:
            props = [method for method in class_.methods if method.is_property]
            base_props = [method for method in class_.base_methods if method.is_property]

            props_names = set(self._get_method_names(props, suffix=''))
            base_props_names = set(self._get_method_names(base_props, suffix='')).difference(props_names)

            methods_str += _get_block_str(sorted(props_names), symbol='+', keep_private=self.keep_private)
            methods_str += f"{_get_block_str(sorted(base_props_names), symbol='-', keep_private=self.keep_private)}|"

            methods = [method for method in class_.methods if not method.is_property]
            base_methods = [method for method in class_.base_methods if not method.is_property]

        else:
            methods = class_.methods
            base_methods = class_.base_methods

        methods_names = set(self._get_method_names(methods))
        base_methods_names = set(self._get_method_names(base_methods)).difference(methods_names)

        methods_str += _get_block_str(sorted(methods_names), symbol='+', keep_private=self.keep_private)
        methods_str += _get_block_str(sorted(base_methods_names), symbol='-', keep_private=self.keep_private)

        return methods_str

    def _get_method_names(self, methods, suffix='()'):
        return [f'{method.short_name}{suffix}' for method in methods]


DEFAULT_RECORD_CREATOR = RecordCreator


def create_graph(classes, record_creator=None, filters=()):
    if record_creator is None:
        record_creator = DEFAULT_RECORD_CREATOR()

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


def save_graph(dot, filename, view=True, format='svg', cleanup=True, **kwargs):
    dot.render(filename, view=view, format=format, cleanup=cleanup, **kwargs)
