
import importlib


def import_class_from_str(import_):
    *module_ls, class_name = import_.split('.')

    module_name = '.'.join(module_ls)
    return getattr(importlib.import_module(module_name), class_name)
