from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

_DATA_EXCLUDE_LIST = ["self", "cls"]


def _generate_data(
    exclude: Optional[List[str]] = None, is_payload: bool = True, **kwargs
) -> Union[Dict[str, Any], str]:
    """
    Generate payload or urlencoded strings based on the provided arguments.

    :param exclude: List of keys to exclude
    :param is_payload: Boolean flag indicating whether to generate payload or path
    :param kwargs: Additional key-value pairs
    :return: dict or str
    """
    if exclude is None:
        exclude = []

    data = {
        key.rstrip("_"): value
        for key, value in kwargs.items()
        if key not in exclude + _DATA_EXCLUDE_LIST
        and value is not None
        and not key.startswith("_")
    }

    if is_payload:
        return data
    else:
        return urlencode(data)
