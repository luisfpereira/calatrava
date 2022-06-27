
import abc
import json


def apply_filters(filters, classes):
    filtered_classes = classes.copy()

    for filter_ in filters:
        filter_.filter(filtered_classes)

    return filtered_classes


class Filter(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def filter(self, classes):
        pass


def load_filters_from_json(filename):

    with open(filename) as file:
        filters_info = json.load(file)

    filters_ls = filters_info.get('filters')
    # TODO: load non-calatrava filters
    # TODO: add concept of order? (useful for non-calatrava)
    return load_filters_from_ls(filters_ls)


def load_filters_from_ls(filters_meta):
    return [load_filter_from_dict(filter_meta) for filter_meta in filters_meta if filter_meta.get('active', True)]


def load_filter_from_dict(filter_meta):
    Filter_ = globals()[filter_meta.get('type')]

    kwargs = filter_meta.copy()
    del kwargs['type']
    kwargs.pop('active', None)

    return Filter_(**kwargs)


class ByNameRemover(Filter):

    def __init__(self, names, attr_name='full_name'):
        self.names = names
        self.attr_name = attr_name

    def filter(self, classes):
        for class_ in classes.copy():
            for name in self.names:
                if getattr(class_, self.attr_name) == name:
                    classes.remove(class_)
                    break


class ByPartialNameRemover(Filter):

    def __init__(self, names, attr_name='full_name'):
        self.names = names
        self.attr_name = attr_name

    def filter(self, classes):
        for class_ in classes.copy():
            for name in self.names:
                if name in getattr(class_, self.attr_name):
                    classes.remove(class_)
                    break


class ByPartialNameKeeper(Filter):
    def __init__(self, names, attr_name='full_name', exceptions=()):
        self.names = names
        self.attr_name = attr_name
        self.exceptions = set(exceptions)

    def filter(self, classes):
        for class_ in classes.copy():
            for name in self.names:
                if name not in getattr(class_, self.attr_name):
                    classes.remove(class_)
                    break


class LoneParentsRemover(Filter):

    def filter(self, classes):
        for class_ in classes.copy():
            if class_.children:
                for child in class_.children:
                    if child in classes:
                        break
                else:
                    classes.remove(class_)
