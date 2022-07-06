
import os
import logging

from git import Repo  # gitpython

from calatrava.scripts import draw_uml

from utils import (
    load_data,
    get_config_file,
    get_output_filename,
    get_imports,
    get_repo_url,
    get_additional_graph_data,
    GRAPHS_DIR,
)

TMP_DIR = '_tmp'


def clone_repo(repo_name, repo_data):
    repo_url = get_repo_url(repo_data)
    repo_dir = os.path.join(TMP_DIR, repo_name)
    if not os.path.exists(repo_dir):
        Repo.clone_from(repo_url, repo_dir)

    return repo_dir


def draw_graph(repo_name, repo_dir, graph_data):
    if not graph_data.get("draw", True):
        return

    config_file = get_config_file(graph_data)
    output_filename = get_output_filename(graph_data, repo_name)
    imports = get_imports(repo_name, repo_dir, graph_data)

    draw_uml(imports, output_filename=output_filename, config=config_file,
             view=False)


if __name__ == '__main__':

    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(GRAPHS_DIR, exist_ok=True)

    data = load_data()

    for repo_name in data:
        logging.info(f"Starting {repo_name}...")

        repo_data = data.get(repo_name)

        repo_dir = clone_repo(repo_name, repo_data)

        draw_graph(repo_name, repo_dir, repo_data)

        # draw additional
        graph_data = get_additional_graph_data(repo_data)

        for graph_data_ in graph_data:
            draw_graph(repo_name, repo_dir, graph_data_)
