
import click
import logging

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
    packages = []
    imports = []

    for arg in args:
        if len(arg.split('.')) > 1:
            imports.append(arg)
        else:
            packages.append(arg)

    return packages, imports


@click.group()
def main_cli():
    pass


@click.command()
@click.argument("args", nargs=-1, type=str, required=True)
@click.option("--output-filename", "-o", type=str,
              default="calatrava_tree")
@click.option("--output-format", type=str, default='svg')
@click.option("--config", '-c', type=str, default=None)
def uml(args, output_filename, output_format, config):
    """Builds UML diagram.
    """
    packages_paths, imports = _handle_variadic_input(args)

    packages = [Package(package_path) for package_path in packages_paths]
    package_manager = PackageManager(packages)

    if imports:
        for import_ in imports:
            package_manager.find(import_)
    else:
        package_manager.find_all()

    package_manager.update_inheritance()

    classes = sorted(list(package_manager.get_classes().values()),
                     key=lambda x: x.name)

    record_creator, filters = load_from_config(config)

    dot = create_graph(classes, filters=filters, record_creator=record_creator)

    save_graph(dot, output_filename, view=True, format=output_format)
    logging.info(f"Created `{output_filename}.{output_format}`")


main_cli.add_command(uml)
