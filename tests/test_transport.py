import pytest

from luxmed.errors import LuxMedAuthenticationError
from luxmed.transport import LuxMedTransport


@pytest.mark.vcr('unauthenticated.yaml')
def test_failed_authentication(app_uuid, client_uuid):
    with pytest.raises(LuxMedAuthenticationError):
        LuxMedTransport(
            user_name='user',
            password='badpassword',
            app_uuid=app_uuid,
            client_uuid=client_uuid).authenticate()


@pytest.mark.vcr('authenticated.yaml')
def test_authentication(app_uuid, client_uuid):
    transport = LuxMedTransport(
        user_name='user',
        password='password',
        app_uuid=app_uuid,
        client_uuid=client_uuid)
    transport.authenticate()
    assert transport.TOKEN_HEADER_NAME in transport._session.headers
