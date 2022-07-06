
from pathlib import Path
import shutil
import os

from utils import (
    load_data,
    get_config_file,
    get_output_filename,
    get_repo_url,
    get_additional_graph_data,
    get_description,
    GRAPHS_DIR,
)

ROOT_DIR = Path('../../')
DOCS_SOURCE_DIR = Path('../source')
PACKAGE_URL = "https://raw.githubusercontent.com/lpereira95/calatrava/master"


def get_config_url(graph_data):
    config_file = get_config_file(graph_data)
    config_short_name = config_file.split(os.path.sep)[-1]
    return f"_configs/{config_short_name}"


def get_image_path(graph_data, repo_name=None, relative_to=DOCS_SOURCE_DIR):
    output_filename = get_output_filename(graph_data, repo_name)
    print(output_filename)
    return Path(output_filename).relative_to(relative_to)


def get_image_url(graph_data, repo_name=None):
    image_path = get_image_path(graph_data, repo_name, relative_to=GRAPHS_DIR)
    return f"_images/{image_path}.svg"


def get_repo_main_text(repo_name, repo_data):
    repo_url = get_repo_url(repo_data)

    config_url = get_config_url(repo_data)

    image_path = get_image_path(repo_data, repo_name)

    space = ' '

    title = f'`{repo_name} <{repo_url}>`_'
    title_mark = f"{len(title)*'='}\n"
    image = f'.. image:: {image_path}.svg\n{space*4}:target: {config_url}'

    return '\n'.join([title, title_mark, image])


def get_simple_case_bullet(graph_data):
    image_url = get_image_url(graph_data)
    config_url = get_config_url(graph_data)

    image_name = image_url.split('/')[-1]
    config_name = config_url.split('/')[-1]

    bullet = f"* `{image_name} <{image_url}>`_ | `{config_name} <{config_url}>`_"
    description = get_description(graph_data)
    if description:
        bullet += f": {description}"

    return bullet


def get_repo_text(repo_name, repo_data):
    main_text = get_repo_main_text(repo_name, repo_data)

    # do additions additional
    graph_data = get_additional_graph_data(repo_data)

    bullets = [get_simple_case_bullet(graph_data_) for graph_data_ in graph_data]
    if bullets:
        text = '\nOther examples:\n\n'
        text += '\n'.join(bullets)
    else:
        return main_text

    return '\n\n'.join([main_text, text])


def main(move=False):
    rst_filename = '_data.rst'

    data = load_data()

    text_ls = [get_repo_text(repo_name, repo_data) for repo_name, repo_data in data.items()]

    text = '\n\n\n'.join(text_ls)

    with open(rst_filename, 'w') as file:
        file.write(text)

    if move:
        shutil.move(rst_filename, os.path.join(DOCS_SOURCE_DIR, rst_filename))


if __name__ == '__main__':
    main(move=True)
