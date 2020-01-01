from datetime import date
from datetime import timedelta
from typing import Dict
from typing import List
from typing import Union


def find_link_rel(links: List, name: str) -> Union[Dict, None]:
    """Returns link with given relation name."""
    for link in links:
        if link['Rel'] == name:
            return link


def year_ago(from_date: date = None) -> date:
    if from_date is None:
        from_date = date.today()
    return from_date - timedelta(days=365)
