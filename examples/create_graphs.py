
import os
import json

from git import Repo  # gitpython

from calatrava.scripts import draw_uml

TMP_DIR = '_tmp'


def load_data(filename):
    with open(filename, "r") as file:
        data = json.load(file)

    return data


def clone_repo(repo_name, repo_data):
    repo_url = repo_data.get("repo_url")
    repo_dir = os.path.join(TMP_DIR, repo_name)
    if not os.path.exists(repo_dir):
        Repo.clone_from(repo_url, repo_dir)

    return repo_dir


def draw_graph(repo_name, repo_dir, graph_data):
    config_file = os.path.join(
        "configs", graph_data.get("config", "config.json")
    )

    output_filename = os.path.join(
        "graphs", graph_data.get("graph_name", repo_name)
    )

    imports = graph_data.get("imports", [])
    if "package_folders" in graph_data:
        imports.extend([os.path.join(repo_dir, folder)
                        for folder in graph_data.get("package_folders")])
    else:
        imports.append(os.path.join(
            repo_dir, graph_data.get("package_folder", f"{repo_name}")))

    draw_uml(imports, output_filename=output_filename, config=config_file,
             view=False)


if __name__ == '__main__':

    metadata_file = "examples.json"

    os.makedirs(TMP_DIR, exist_ok=True)

    data = load_data(metadata_file)

    for repo_name in data:
        repo_data = data.get(repo_name)

        repo_dir = clone_repo(repo_name, repo_data)

        graph_data = repo_data

        draw_graph(repo_name, repo_dir, graph_data)
