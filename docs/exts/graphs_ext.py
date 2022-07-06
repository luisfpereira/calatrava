
import os
import sys
import shutil

GRAPHS_DIR = os.path.join("source", "_graphs")
CONFIGS_DIR = os.path.join("examples", "configs")


def setup(app):

    app.add_config_value(
        'generate_graphs',
        default=True,
        rebuild=False,
    )

    app.connect('builder-inited', startup)
    app.connect('build-finished', cleanup)


def startup(app):
    if not app.builder.config.generate_graphs:
        return

    examples_dir = "examples"
    sys.path.insert(0, os.path.abspath(examples_dir))

    cwd = os.getcwd()
    os.chdir(examples_dir)

    from create_graphs import main as create_graphs_
    from create_rst import main as create_rst_

    create_graphs_()
    create_rst_(move=True)

    os.chdir(cwd)


def cleanup(app, exception):
    if not app.builder.config.generate_graphs:
        return

    outdir = app.builder.outdir
    images_dir = os.path.join(outdir, '_images')
    _copy_files(GRAPHS_DIR, images_dir)

    configs_dir = os.path.join(outdir, '_configs')
    os.makedirs(configs_dir, exist_ok=True)
    _copy_files(CONFIGS_DIR, configs_dir)


def _copy_files(source, destination):
    for filename in os.listdir(source):
        new_name = os.path.join(destination, filename)
        if os.path.exists(new_name):
            continue

        previous_name = os.path.join(source, filename)
        shutil.copy(previous_name, new_name)
