import pytest

from luxmed.errors import LuxMedAuthenticationError
from luxmed.transport import LuxMedTransport


def test_authentication(authenticated_transport):
    assert authenticated_transport.TOKEN_HEADER_NAME in authenticated_transport._session.headers


@pytest.mark.vcr('unauthenticated.yaml')
def test_failed_authentication(app_uuid, client_uuid):
    with pytest.raises(LuxMedAuthenticationError):
        LuxMedTransport(
            user_name='user',
            password='badpassword',
            app_uuid=app_uuid,
            client_uuid=client_uuid).authenticate()
