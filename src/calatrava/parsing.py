

import os
from pathlib import Path
import glob
import warnings

import findimports

from xlizard import (
    load_content,
    parse_content,
)

# TODO: everything needs to be rethought
# TODO: parse also class attributes
# TODO: organize classes alphabetically
# TODO: extend to multiple projects


def _update_context_names(context, path, project_loc):
    # update functions names
    context_name = str(Path(path).parent.relative_to(project_loc))
    context_name = context_name.replace(os.sep, '.')

    previous_name = context.global_pseudo_function.name
    context.global_pseudo_function.name = f'{context_name}.{previous_name}'
    for function in context.fileinfo.function_list:
        function.name = f'{context_name}.{function.name}'


def _create_class_list(context):
    function_list = context.fileinfo.function_list
    class_list = context.fileinfo.class_list = []

    # TODO: make it work with nested classes?
    # TODO: make it work with nested functions
    methods = []
    for function in function_list.copy():
        if function.type == 'class_method':
            methods.append(function)
            function_list.remove(function)

        elif function.type == 'class':
            function.methods = methods
            methods = []
            class_list.append(function)
            function_list.remove(function)


def _create_class_attrs(context):
    for cls in context.fileinfo.class_list:
        attrs = _get_instance_attrs(cls)

        cls.attrs = attrs


def _get_instance_attrs(cls):

    attrs = []
    for method in cls.methods:
        # assumes use of self
        for var in method.local_vars:
            if var.count('.') == 1 and var.split('.')[0] == 'self':
                attrs.append(var.split('.')[1])

    return attrs


def _update_classes_inheritance(context, imports):
    context_name = context.global_pseudo_function.name

    context_cls_names = [cls.name for cls in context.fileinfo.class_list]

    for cls in context.fileinfo.class_list:
        _update_base_cls_names(cls, context_name, context_cls_names,
                               imports)


def _update_base_cls_names(cls, context_name, context_cls_names, imports):
    base_classes = []
    for base_cls_name in cls.base_classes.copy():
        new_name = f'{context_name}.{base_cls_name}'

        if new_name in context_cls_names:  # defined in module
            base_classes.append(new_name)

        else:  # imported
            for name in imports:
                if name.split('.')[-1].endswith(base_cls_name):
                    base_classes.append(name)
                    break

            else:
                # TODO: may go wrong with abc
                warnings.warn(f'Cannot find {base_cls_name} in imports...')

    cls.base_classes = base_classes


def _get_module_import(filename, project_loc):
    module_path = str(Path(filename).relative_to(project_loc))
    return '.'.join(module_path.split('.')[0].split(os.sep))


def _get_path_from_obj_import(object_import, project_loc):
    return _get_path_from_module_import(
        '.'.join(object_import.split('.')[:-1]), project_loc)


def _get_path_from_module_import(module_name, project_loc):
    return os.path.join(project_loc, f"{module_name.replace('.', os.sep)}.py")


def _transform_relative_imports(module_name, imports):
    corrected_imports = []
    for import_ in imports:
        if import_.level:
            import_.name = '.'.join(module_name.split('.')[:-import_.level] + import_.name.split('.'))

        corrected_imports.append(import_)

    return corrected_imports


def _correct_imports_from_init(imports, project_loc, project_name):
    # TODO: correct for recursive errors
    corrected_imports = []
    for import_ in imports:
        if not import_.name.startswith(project_name):
            corrected_imports.append(import_)
            continue

        filename = _get_path_from_module_import(import_.name, project_loc)
        if not os.path.exists(filename):
            filename = _get_path_from_obj_import(import_.name, project_loc).split('.')[0]

            if os.path.isdir(filename):
                filename += f'{os.sep}__init__.py'
                init_imports = _get_imports(filename, project_loc)

                for init_import in init_imports:
                    if init_import.split('.')[-1] == import_.name.split('.')[-1]:
                        import_.name = init_import
                        break

        corrected_imports.append(import_)

    return corrected_imports


def _correct_import_from_init():
    pass


def _get_imports(filename, project_loc):
    # TODO: use caching
    # TODO: _update_imports_from_imports
    g = findimports.ModuleGraph()
    g.external_dependencies = True
    g.parsePathname(filename)

    # assuming only one module
    module = g.listModules()[0]

    module_import = _get_module_import(filename, project_loc)
    imports = _transform_relative_imports(module_import, module.imported_names)

    # # correct init imports
    # imports = _correct_imports_from_init(
    #     imports, project_loc, module_import.split('.')[0])

    return [imp.name for imp in imports]


def get_context(path, project_loc):
    """Get file context.
    """
    content = load_content(path)

    context = parse_content(path, content)

    # TODO: abstract better (from_flinter?)
    _update_context_names(context, path, project_loc)
    _create_class_list(context)
    _create_class_attrs(context)
    imports = _get_imports(path, project_loc)
    _update_classes_inheritance(context, imports)

    return context


def find_class(project_name, project_loc, main_cls_name,
               contexts, existing_classes):
    """Get class and all its dependencies (within the package).
    """
    if main_cls_name in existing_classes:
        main_cls = existing_classes[main_cls_name]
        _find_base_classes(main_cls, project_name, project_loc,
                           contexts, existing_classes)
        return

    if main_cls_name in existing_classes:
        main_cls = existing_classes[main_cls_name]

    else:
        class_path = ".".join(main_cls_name.split('.')[:-1]).replace('.', os.sep)

        # TODO: improve (is buggy)
        dir_path = f'{project_loc}{os.sep}{class_path}'
        if os.path.isdir(dir_path):  # is __init__
            init_imports = _get_imports(
                f'{project_loc}{os.sep}{class_path}/__init__.py',
                project_loc)

            for init_import in init_imports:
                if init_import.split('.')[-1] == main_cls_name.split('.')[-1]:
                    class_path = ".".join(init_import.split('.')[:-1]).replace('.', os.sep)
                    break
            else:
                raise Exception(f'Cannot find {main_cls_name}')

        while True:
            if class_path == '':
                raise Exception(f'Cannot find {main_cls_name}')
            try:
                path = f'{project_loc}{os.sep}{class_path}.py'
                main_context = get_context(path, project_loc)
                break
            except FileNotFoundError:
                class_path = f"{os.sep}".join(class_path.split(os.sep)[:-1])

        # get context
        contexts[main_context.global_pseudo_function.name] = main_context
        existing_classes.update({cls.name: cls for cls in main_context.fileinfo.class_list})

        # get main class
        for cls in main_context.fileinfo.class_list:
            if cls.name == main_cls_name:
                main_cls = cls
                break
        else:
            # TODO: improve to show them anyway?
            warnings.warn(f'{main_cls_name} imported from external package')
            return

    # find base classes
    _find_base_classes(main_cls, project_name, project_loc, contexts, existing_classes)


def find_classes(project_name, project_loc, main_cls_names,
                 context, existing_classes):
    for main_cls_name in main_cls_names:
        find_class(project_name, project_loc, main_cls_name,
                   context, existing_classes)


def _find_base_classes(main_cls, project_name, project_loc,
                       contexts, existing_classes):

    for cls_name in main_cls.base_classes:
        if cls_name in existing_classes:
            cls = existing_classes[cls_name]
            _find_base_classes(cls, project_name, project_loc, contexts, existing_classes)

        elif cls_name.split('.')[0] != project_name:  # TODO: create dummy
            # for now ignores outside classes
            # TODO: extract abstract info
            continue

        else:
            # start search process
            find_class(project_name, project_loc, cls_name, contexts, existing_classes)


def _get_context_cls_names(context):
    return [cls.name for cls in context.fileinfo.class_list]


def parse_module(project_name, project_loc, module_name,
                 contexts, existing_classes):

    if module_name in contexts:
        context = contexts[module_name]
        return _get_context_cls_names(context)

    path = _get_path_from_module_import(module_name, project_loc)
    context = get_context(path, project_loc)
    contexts[context.global_pseudo_function.name] = context
    existing_classes.update({cls.name: cls for cls in context.fileinfo.class_list})

    # find inheritance
    main_cls_names = _get_context_cls_names(context)
    find_classes(project_name, project_loc, main_cls_names,
                 contexts, existing_classes)

    return main_cls_names


def parse_modules(project_name, project_loc, module_names,
                  contexts, existing_classes):
    main_cls_names = []
    for module_name in module_names:
        main_cls_names_ = parse_module(
            project_name, project_loc, module_name,
            contexts, existing_classes)
        main_cls_names.extend(main_cls_names_)

    return list(set(main_cls_names))


def parse_subpackage(project_name, project_loc, subpackage_name,
                     contexts, existing_classes):

    # assumes all used classes belong to module
    dirname = f"{project_loc}{os.sep}{subpackage_name.replace('.', os.sep)}"
    paths = glob.glob(f'{dirname}/**/*.py', recursive=True)

    module_names = [str(Path(path).relative_to(project_loc)).split('.')[0].replace(os.sep, '.')
                    for path in paths]

    return parse_modules(project_name, project_loc, module_names,
                         contexts, existing_classes)


def parse_subpackages(project_name, project_loc, subpackage_names,
                      contexts, existing_classes):

    main_cls_names = []
    for subpackage_name in subpackage_names:
        main_cls_names_ = parse_subpackage(
            project_name, project_loc, subpackage_name,
            contexts, existing_classes)
        main_cls_names.extend(main_cls_names_)

    return list(set(main_cls_names))


def parse_package(project_name, project_loc,
                  contexts, existing_classes):
    return parse_subpackage(project_name, project_loc, project_name,
                            contexts, existing_classes)
