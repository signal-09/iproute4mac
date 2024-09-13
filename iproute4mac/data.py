def isnumber(value):
    return isinstance(value, int | float | complex)


def empty(value):
    """
    Empty values are: None, "", (), [], {}
    Note: 0 is not evaluated as empty
    """
    return value is None or (not isnumber(value) and not value)


def _get_item(data, key):
    value = None
    if key in data:
        return True, data[key]
    else:
        for key, value in data.items():
            if isinstance(value, dict):
                found, res = _get_item(value, key)
                if found:
                    return True, res
    return False, None


def get_item(data, key, default=None):
    """
    Recurse search for `key` in `data` dict

    Input:
    `data` dictionary to search in
    `key` key to find
    """
    found, res = _get_item(data, key)
    return res if found else default


def find_item(data, key, value=None, recurse=True, strict=False):
    """
    Search for `key` in `data` dict

    Input:
    `data` dictionary to search in
    `key` key to find
    `value` (optional) specific value to find
    `strict` (optional) return bool(value) (e.g. True/False instead of "", [], {})
    """
    if key in data:
        if value is not None:
            return data[key] == value
        if strict:
            return isnumber(data[key]) or bool(data[key])
        return data[key] is not None
    if recurse:
        for k, v in data.items():
            if isinstance(v, dict):
                if find_item(v, key, value=value, recurse=recurse, strict=strict):
                    return True
    return False


def dict_format(data, string, *fields, default=None):
    if not data or not fields or empty(data.get(fields[0], default)):
        return ""
    return string.format(*[data.get(field, default) for field in fields])


def delete_keys(data, *keys, recurse=False):
    for item in data:
        for key in keys:
            item.pop(key, None)
        else:
            if recurse and isinstance(data[key], dict):
                delete_keys(data[key], *keys, True)


def list_filter(data):
    """
    Return the list without empty values
    """
    res = []
    for value in data:
        if isinstance(value, dict):
            value = dict_filter(value)
        elif isinstance(value, list):
            value = list_filter(value)
        if not empty(value):
            res.append(value)
    return res


def dict_filter(data):
    """
    Return the dictionary without empty values
    """
    res = {}
    for key, value in data.items():
        if isinstance(value, dict):
            value = dict_filter(value)
        elif isinstance(value, list):
            value = list_filter(value)
        if not empty(value):
            res[key] = value
    return res


def filter_empty(data):
    if isinstance(data, list):
        return list_filter(data)
    if isinstance(data, dict):
        return dict_filter(data)
    raise ValueError


class _Item:
    """
    Iterable dictionary of data
    """

    __slots__ = ("_data",)
    _OPTIONAL_FIELDS = {
        # key: value
    }

    def __init__(self):
        raise NotImplementedError

    def __str__(self):
        return self.str()

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, key):
        return self._data.get(key)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        if key in self._data:
            del self._data[key]

    def get(self, key, default=None, recurse=False):
        return get_item(self._data, key, default) if recurse else self._data.get(key, default)

    def pop(self, key, default=None):
        if default is None:
            return self._data.pop(key)
        return self._data.pop(key, default)

    def present(self, key, value=None, recurse=False, strict=False):
        return find_item(self._data, key, value=value, recurse=recurse, strict=strict)

    def data(self, details=True):
        """
        Raw data, without empty values and, eventually, without optional fields
        """
        res = {}
        for key, value in self._data.items():
            if value is None:
                continue
            if not details and key in self._OPTIONAL_FIELDS:
                if self._OPTIONAL_FIELDS[key] is None or self._OPTIONAL_FIELDS[key] == value:
                    continue
            res[key] = value
        return res

    def _cast(self, value):
        if value.isdigit():
            return int(value)
        if value.replace(".", "", 1).isdigit():
            return float(value)
        if value == "<none>":
            return None
        if value.lower() in ["true", "yes", "enabled"]:
            return True
        if value.lower() in ["false", "no", "disabled"]:
            return False
        return value

    def _value(self, key, value):
        if isinstance(value, dict):
            return self._dict(value)
        if isinstance(value, list):
            return self._list(value)
        if isinstance(value, str):
            return self._cast(value)
        # numbers|class|...
        return value

    def _list(self, data):
        res = []
        for value in data:
            if isinstance(value, dict):
                value = self._dict(value)
            elif isinstance(value, list):
                value = self._list(value)
            elif value is not None:
                value = self._cast(value)
            res.append(value)
        return res

    def _dict(self, data):
        res = {}
        for key, value in data.items():
            value = self._value(key, value)
            if not empty(value):
                res[key] = value
        return res

    def dict(self, details=True):
        return self._dict(self.data(details=details))

    def str(self, details=True):
        raise NotImplementedError


class _Items:
    """
    Iterable list of dictionaries
    """

    __slots__ = ("_data",)

    def __init__(self):
        raise NotImplementedError

    def __iter__(self):
        for item in self._data:
            yield item

    def __str__(self):
        return "\n".join(map(str, self._data))

    def __len__(self):
        return len(self._data)

    def __getitem__(self, index):
        return self._data[index]

    def pop(self, index=-1):
        return self._data.pop(index)

    def append(self, item):
        if not isinstance(item, _Item):
            raise ValueError("item is not of {_Item}")
        if hasattr(self, "_data"):
            self._data.append(item)
        else:
            self._data = [item]

    def set(self, data):
        # all(instance(...)) also accept empty list ([]) as valid
        if not isinstance(data, list) or not all(isinstance(item, _Item) for item in data):
            raise ValueError("data is not list() of {_Item}")
        self._data = data

    def lookup(self, key, value):
        return next((item for item in self._data if item.present(key, value)), None)

    def dict(self, details=None):
        return [item.dict(details=details) for item in self._data]

    # alias self.list() as self.dict()
    list = dict

    def str(self, details=None):
        return "\n".join([item.str(details=details) for item in self._data])
