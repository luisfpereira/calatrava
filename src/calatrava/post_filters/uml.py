
import abc

from calatrava.utils import import_class_from_str


def apply_filters(filters, classes):
    # mutable
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


def _find_connected(class_, related=None, ignore=()):
    if related is None:
        related = []

    for child in class_.bases + class_.children:
        if child not in ignore and child not in related:
            related.append(child)
            _find_connected(child, related=related, ignore=ignore)

    return related


def _find_related(class_, related=None, ignore=(), look_down=True):
    if related is None:
        related = []

    for child in class_.bases:
        if child not in ignore and child not in related:
            related.append(child)
            _find_related(child, related=related, ignore=ignore,
                          look_down=False)

    if not look_down:
        return related

    for child in class_.children:
        if child not in ignore and child not in related:
            related.append(child)
            _find_related(child, related=related, ignore=ignore,
                          look_down=True)

    return related


def _remove_unrelated(classes, related):
    for class_ in classes.copy():
        if class_ not in related:
            classes.remove(class_)

    return classes


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


class ConnectedKeeper(Filter):

    def __init__(self, names, attr_name='name', ignore=('abc.ABC', 'abc.ABCMeta',)):
        self.names = names
        self.attr_name = attr_name
        self.ignore = ignore

    def filter(self, classes):
        main_classes = _find_classes_by_attr(
            classes, self.names, self.attr_name
        )
        ignore = _find_classes_by_attr(classes, self.ignore, "long_name")

        related = []
        for main_class in main_classes:
            _find_connected(main_class, related=related, ignore=ignore)

        return _remove_unrelated(classes, set(related))


class RelatedKeeper(Filter):

    def __init__(self, names, attr_name='name', ignore=('abc.ABC', 'abc.ABCMeta',),
                 find_related=None):
        self.names = names
        self.attr_name = attr_name
        self.ignore = ignore

        if find_related is None:
            find_related = _find_related

        self.find_related = find_related

    def filter(self, classes):
        main_classes = _find_classes_by_attr(
            classes, self.names, self.attr_name
        )
        ignore = _find_classes_by_attr(classes, self.ignore, "long_name")

        all_related = []
        for main_class in main_classes:
            related = self.find_related(main_class, ignore=ignore)
            all_related.extend(related)

        return _remove_unrelated(classes, set(all_related))


class AbstractKeeper(Filter):
    def filter(self, classes):
        for class_ in classes.copy():
            if not class_.is_abstract:
                classes.remove(class_)

        return classes
