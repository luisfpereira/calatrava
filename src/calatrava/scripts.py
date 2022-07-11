
import logging
import os

from calatrava.config import load_from_config
from calatrava.viz.graphviz.uml import (
    create_graph,
    save_graph,
)
from calatrava.parser.ast.uml import (
    Package,
    PackageManager,
)

logging.basicConfig(format='%(message)s', level=logging.INFO)


def _handle_variadic_input(args):
    package_names = []

    packages = []
    imports = []

    args = list(args)
    while len(args) > 0:
        arg = args.pop(0)

        if len(arg.split('.')) > 1 or arg in package_names:
            imports.append(arg)
        else:
            package_names.append(arg.split(os.sep)[-1])
            packages.append(arg)

    return packages, imports


def parse_packages(args):
    packages_paths, imports = _handle_variadic_input(args)

    packages = [Package(package_path) for package_path in packages_paths]
    package_manager = PackageManager(packages)

    if imports:
        for import_ in imports:
            if len(import_.split('.')) > 1:
                package_manager.find(import_)
            else:
                package_manager.find_package(import_)
    else:
        package_manager.find_all()

    package_manager.update_inheritance()

    return package_manager


def draw_uml(args, output_filename="calatrava_tree", output_format="svg",
             config=None, view=True):

    package_manager = parse_packages(args)

    classes = sorted(list(package_manager.get_classes().values()),
                     key=lambda x: x.name)

    record_creator, filters = load_from_config(config)

    dot = create_graph(classes, filters=filters, record_creator=record_creator)

    save_graph(dot, output_filename, view=view, format=output_format)
    logging.info(f"Created `{output_filename}.{output_format}`")
