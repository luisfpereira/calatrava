

# TODO: add methods and attributes filters


def apply_filters(filters, existing_classes):
    filtered_cls_names = []
    for filter_ in filters:
        filtered_cls_names.extend(filter_(existing_classes))

    return filtered_cls_names


def remove_parametrizer(existing_classes):
    parametrizer_name = 'tests.conftest.Parametrizer'

    if parametrizer_name in existing_classes:
        del existing_classes[parametrizer_name]

    return [parametrizer_name]


def remove_metric(existing_classes):

    filtered_cls_names = []
    for key in list(existing_classes.keys()):
        if not ('Metric' not in key and 'Connection' not in key):
            filtered_cls_names.append(key)
            del existing_classes[key]

    return filtered_cls_names


def remove_not_metric(existing_classes):
    # filter not metric out
    filtered_cls_names = []
    for key in list(existing_classes.keys()):
        if 'Metric' not in key and 'Connection' not in key:
            filtered_cls_names.append(key)
            del existing_classes[key]

    return filtered_cls_names
