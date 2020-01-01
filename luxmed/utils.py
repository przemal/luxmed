from typing import Dict
from typing import List
from typing import Union


def find_link_rel(links: List, name: str) -> Union[Dict, None]:
    """Returns link with given relation name."""
    for link in links:
        if link['Rel'] == name:
            return link
