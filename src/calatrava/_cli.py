
import importlib
import click


from calatrava.graphviz import (
    create_graph,
    save_graph,
)
from calatrava.filters import apply_filters


def add_options(options):
    # https://stackoverflow.com/a/40195800/11011913
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


_proj_name_arg = click.argument("project_name", type=str, required=True)
_proj_loc_arg = click.argument("project_loc", type=click.Path(exists=True),
                               required=True)
_mandatory_args = [_proj_name_arg, _proj_loc_arg]


_output_filename_opt = click.option("--output-filename", "-o", type=str,
                                    default="calatrava_tree")
_output_format_opt = click.option("--output-format", type=str, default='svg')
_filters = click.option("--filters", '-f', type=str, multiple=True, default=())
_common_options = [_output_filename_opt, _output_format_opt, _filters]


def _load_filters(filter_names):
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


@click.group()
def main_cli():
    pass


@click.command()
@add_options(_mandatory_args)
@add_options(_common_options)
def project(project_name, project_loc, filters,
            output_filename, output_format):

    from calatrava.parsing import parse_package

    contexts = {}
    existing_classes = {}

    main_cls_names = parse_package(
        project_name, project_loc,
        contexts, existing_classes
    )

    _filter_and_draw(main_cls_names, existing_classes, filters,
                     output_filename, output_format)


main_cli.add_command(project)


@click.command()
@add_options(_mandatory_args)
@click.argument("subpackage_names", nargs=-1, type=str, required=True)
@add_options(_common_options)
def subpackages(project_name, project_loc, subpackage_names, filters,
                output_filename, output_format):

    from calatrava.parsing import parse_subpackages

    print(subpackage_names)

    contexts = {}
    existing_classes = {}

    main_cls_names = parse_subpackages(
        project_name, project_loc, subpackage_names,
        contexts, existing_classes
    )

    _filter_and_draw(main_cls_names, existing_classes, filters,
                     output_filename, output_format)


main_cli.add_command(subpackages)


@click.command()
@add_options(_mandatory_args)
@click.argument("module_names", nargs=-1, type=str, required=True)
@add_options(_common_options)
def modules(project_name, project_loc, module_names, filters,
            output_filename, output_format):

    from calatrava.parsing import parse_modules

    contexts = {}
    existing_classes = {}

    main_cls_names = parse_modules(
        project_name, project_loc, module_names,
        contexts, existing_classes
    )

    _filter_and_draw(main_cls_names, existing_classes, filters,
                     output_filename, output_format)


main_cli.add_command(modules)


@click.command()
@add_options(_mandatory_args)
@click.argument("class_names", nargs=-1, type=str, required=True)
@add_options(_common_options)
def classes(project_name, project_loc, class_names, filters,
            output_filename, output_format):

    from calatrava.parsing import find_classes

    contexts = {}
    existing_classes = {}

    find_classes(
        project_name, project_loc, class_names,
        contexts, existing_classes
    )

    _filter_and_draw(class_names, existing_classes, filters,
                     output_filename, output_format)


main_cli.add_command(classes)
