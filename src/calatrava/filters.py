
import abc

from calatrava.utils import import_class_from_str


def apply_filters(filters, classes):
    for filter_ in filters:
        filter_.filter(classes)

    return classes


class Filter(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def filter(self, classes):
        return classes


def load_filters_from_ls(filters_meta):
    return [load_filter_from_dict(filter_meta) for filter_meta in filters_meta if filter_meta.get('active', True)]


def load_filter_from_dict(filter_meta):
    type_ = filter_meta.get('type')
    Filter_ = import_class_from_str(type_) if '.' in type_ else globals().get(type_)

    kwargs = filter_meta.copy()
    del kwargs['type']
    kwargs.pop('active', None)

    return Filter_(**kwargs)


def _find_classes_by_attr(classes, attrs, attr_name="name"):
    return [class_ for class_ in classes if getattr(class_, attr_name) in attrs]


def _find_all_related(class_, related=None, ignore=()):
    if related is None:
        related = []

    for child in class_.bases + class_.children:
        if child not in ignore and child not in related:
            related.append(child)
            _find_all_related(child, related=related, ignore=ignore)

    return related


class PackageRemover(Filter):
    def __init__(self, names):
        self.names = set(names)

    def filter(self, classes):
        for class_ in classes.copy():
            package_name = class_.long_name.split('.')[0]
            if package_name in self.names:
                classes.remove(class_)

        return classes


class ByNameRemover(Filter):

    def __init__(self, names, attr_name='long_name'):
        self.names = set(names)
        self.attr_name = attr_name

    def filter(self, classes):
        for class_ in classes.copy():
            if getattr(class_, self.attr_name) in self.names:
                classes.remove(class_)

        return classes


class ByPartialNameRemover(Filter):

    def __init__(self, names, attr_name='long_name'):
        self.names = set(names)
        self.attr_name = attr_name

    def filter(self, classes):
        for class_ in classes.copy():
            class_name = getattr(class_, self.attr_name)
            for name in self.names:
                if name in class_name:
                    classes.remove(class_)
                    break

        return classes


class ByPartialNameKeeper(Filter):
    def __init__(self, names, attr_name='long_name', exceptions=()):
        self.names = set(names)
        self.attr_name = attr_name
        self.exceptions = set(exceptions)

    def filter(self, classes):
        for class_ in classes.copy():
            class_name = getattr(class_, self.attr_name)
            for name in self.names:
                if name not in class_name:
                    classes.remove(class_)
                    break

        return classes


class LoneParentsRemover(Filter):

    def filter(self, classes):
        for class_ in classes.copy():
            if class_.children:
                for child in class_.children:
                    if child in classes:
                        break
                else:
                    classes.remove(class_)

        return classes


class RelatedOnlyKeeper(Filter):

    def __init__(self, names, attr_name='name',
                 ignore=('abc.ABC', 'abc.ABCMeta',)):
        self.names = names
        self.attr_name = attr_name
        self.ignore = ignore

    def _remove_unrelated(self, classes, related):
        for class_ in classes.copy():
            if class_ not in related:
                classes.remove(class_)

        return classes

    def filter(self, classes):
        parent_classes = _find_classes_by_attr(classes, self.names, self.attr_name)
        ignore = _find_classes_by_attr(classes, self.ignore, "long_name")
        related = []
        for parent_class in parent_classes:
            if parent_class in related:
                continue

            _find_all_related(parent_class, related=related, ignore=ignore)

        return self._remove_unrelated(classes, set(related))
