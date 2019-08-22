from collections import namedtuple

import pytest

from luxmed.transformers import underscored_named_tuple


@pytest.mark.parametrize(
    'source, reference', [({
             'AccountId': 0,
             'FirstName': 'John',
             'LastName': 'Doe',
             'Links': [{
                 'ApiVersion': 1}]
         }, namedtuple('Item', [
            'account_id', 'first_name', 'last_name', 'links'])(0, 'John', 'Doe', [
                namedtuple('Item', 'api_version')(1)]))
    ])
def test_underscored_named_tuple(source, reference):
    """Compares original and converted keys and their values.
    Args:
        source: Original data.
        reference: Transformed data.
    """
    transformed = underscored_named_tuple(source)
    assert transformed._asdict() == reference._asdict() \
        and transformed.links[0]._asdict() == reference.links[0]._asdict()
