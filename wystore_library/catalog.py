"""Editorial settings shared by metadata and APK configuration consumers."""


def foreign_category(entry):
    value = entry.get('foreign_category', True)
    if not isinstance(value, bool):
        raise ValueError('foreign_category must be a boolean')
    return value
