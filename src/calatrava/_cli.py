
import click


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
    from calatrava.scripts import draw_uml

    draw_uml(args, output_filename, output_format, config, view=True)


main_cli.add_command(uml)
