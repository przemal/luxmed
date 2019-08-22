from collections import namedtuple
from datetime import date
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Tuple
from typing import Union

from inflection import camelize
from inflection import underscore


FILTER_DEFAULTS = dict(from_date=lambda: date.today().isoformat())


def full_filter_name(name: str) -> str:
    return 'filter.' + camelize(name)


def filter_args(**kwargs) -> Iterator[Tuple[str, Union[int, str]]]:
    """Converts all given keyword arguments to the proper filters understood by the service API.
    When given argument does not have a value, a default one is used or it is dropped.

    Args:
        **kwargs: Native (internal) keyword arguments with their values.

    Yields:
        Full filter name and a value as a tuple.
    """
    for name, value in kwargs.items():
        if value is None:
            try:
                value = FILTER_DEFAULTS[name]()
            except KeyError:
                continue
        yield full_filter_name(name), value


def map_id_name(data: List[Dict]) -> Dict[int, str]:
    """Simplifies list of dictionaries to a flat dictionary.

    Args:
        data: (list of dict): Dictionary must contain 'Id' and 'Name' keys.

    Returns:
        Simplified dictionary.

    Raises:
        KeyError: Whenever a dictionary misses any of the required keys.
    """
    mapped = {}
    for item in data:
        mapped[item['Id']] = item['Name']
    return mapped


def underscored_named_tuple(data: Any) -> Any:
    """Recursively converts all key names from camel case to underscore and replaces dictionaries with named tuples.

    Args:
        data: Any object.

    Returns:
        Transformed object (or original one, depending on the given type).
    """
    if isinstance(data, Dict):
        for key in list(data.keys()):
            data[underscore(key)] = underscored_named_tuple(data.pop(key))
        return namedtuple('Item', data.keys())(**data)
    elif isinstance(data, List):
        return [underscored_named_tuple(item) for item in data]
    return data
