import os
import json
from pathlib import Path


METADATA_FILE = "examples.json"
GRAPHS_DIR = Path('../source/_graphs')


def load_data(filename=METADATA_FILE):
    with open(filename, "r") as file:
        data = json.load(file)

    return data


def get_repo_url(repo_data):
    return repo_data.get("repo_url")


def get_config_file(graph_data):
    return os.path.join(
        "configs", graph_data.get("config", "config.json")
    )


def get_output_filename(graph_data, repo_name=None):
    return os.path.join(
        GRAPHS_DIR, graph_data.get("graph_name", repo_name)
    )


def get_imports(repo_name, repo_dir, graph_data):
    imports = graph_data.get("imports", [])
    if "package_folders" in graph_data:
        imports.extend([os.path.join(repo_dir, folder)
                        for folder in graph_data.get("package_folders")])
    else:
        imports.append(os.path.join(
            repo_dir, graph_data.get("package_folder", f"{repo_name}")))

    return imports


def get_additional_graph_data(repo_data):
    return repo_data.get("other", [])


def get_description(graph_data):
    return graph_data.get("description", "")
