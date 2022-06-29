
import abc


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
    Filter_ = globals()[filter_meta.get('type')]

    kwargs = filter_meta.copy()
    del kwargs['type']
    kwargs.pop('active', None)

    return Filter_(**kwargs)


class PackageRemover(Filter):
    def __init__(self, names):
        self.names = set(names)

    def filter(self, classes):
        for class_ in classes.copy():
            package_name = class_.full_name.split('.')[0]
            if package_name in self.names:
                classes.remove(class_)

        return classes


class ByNameRemover(Filter):

    def __init__(self, names, attr_name='full_name'):
        self.names = set(names)
        self.attr_name = attr_name

    def filter(self, classes):
        for class_ in classes.copy():
            if getattr(class_, self.attr_name) in self.names:
                classes.remove(class_)

        return classes


class ByPartialNameRemover(Filter):

    def __init__(self, names, attr_name='full_name'):
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
    def __init__(self, names, attr_name='full_name', exceptions=()):
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
