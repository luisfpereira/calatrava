
from pathlib import Path
import json

from calatrava.viz.graphviz.uml import (
    DEFAULT_RECORD_CREATOR,
    load_record_creator_from_dict,
)
from calatrava.filters import load_filters_from_ls


def get_global_config_file():
    path = Path.home() / '.calatrava' / '.config.json'
    if path.exists():
        return str(path)


def load_from_config(filename=None):
    if filename is None:
        filename = get_global_config_file()

    if filename is None:
        return DEFAULT_RECORD_CREATOR(), []

    with open(filename, 'r') as file:
        data = json.load(file)

    # load record
    record_metadata = data.get("record_creator", None)
    if record_metadata is not None:
        record_creator = load_record_creator_from_dict(record_metadata)
    else:
        record_creator = DEFAULT_RECORD_CREATOR()

    # load filters
    filter_metadata = data.get("filters", [])
    filters = load_filters_from_ls(filter_metadata)

    return record_creator, filters
