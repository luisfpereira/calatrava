

import os
from pathlib import Path
import glob

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
