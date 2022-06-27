
import importlib
import click


from calatrava.graphviz.uml import (
    create_graph,
    save_graph,
)
from calatrava.filters import apply_filters


def _load_filters(filter_names):
    # TODO: delete?
    filters_loc = 'calatrava.filters'
    filters_mod = importlib.import_module(filters_loc)
    filters = [getattr(filters_mod, filter_name)
               for filter_name in filter_names]

    return filters


def _filter_and_draw(main_cls_names, existing_classes, filter_names,
                     output_filename, output_format):

    filters = _load_filters(filter_names)
    filtered_cls_names = apply_filters(filters, existing_classes)

    dot = create_graph(existing_classes,
                       main_cls_names=main_cls_names,
                       filtered_cls_names=filtered_cls_names)
    save_graph(dot, output_filename, view=True, format=output_format)


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
@click.option("--filters", '-f', type=str, multiple=True, default=())
def uml(args, output_filename, output_format):
    """Builds UML diagram.
    """
    from calatrava.parser.ast_uml import (
        Package,
        PackageManager,
    )

    packages_paths, imports = _handle_variadic_input(args)

    packages = [Package(package_path) for package_path in packages_paths]
    package_manager = PackageManager(packages)

    if imports:
        for import_ in imports:
            package_manager.find(import_)
    else:
        package_manager.find_all()

    package_manager.update_inheritance()

    classes = package_manager.get_classes().values()
    dot = create_graph(classes)

    save_graph(dot, output_filename, view=True, format=output_format)


main_cli.add_command(uml)
