from urllib.parse import urlsplit

import requests
from cas import CASClientV2
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class CASSession(requests.Session):
    def __init__(self):
        super().__init__()
        # UI's gateway returns HTTP 400 for requests' default User-Agent.
        self.headers["User-Agent"] = "PandaCrumbs/0.2 (UI SSO CAS client)"

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", (3.05, 8))
        kwargs["allow_redirects"] = False
        response = super().request(method, url, **kwargs)
        response.raise_for_status()
        if response.status_code != 200:
            raise requests.HTTPError("Unexpected CAS response", response=response)
        return response


def cas_client(service, session=None):
    server = settings.SSO_UI_SERVER_URL
    parsed = urlsplit(server)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "sso.ui.ac.id"
        or parsed.query
        or parsed.fragment
        or not parsed.path.endswith("/")
    ):
        raise ImproperlyConfigured("SSO_UI_SERVER_URL must be an HTTPS base URL on sso.ui.ac.id.")
    return CASClientV2(
        server_url=server,
        service_url=service,
        session=session,
        verify_ssl_certificate=True,
    )
