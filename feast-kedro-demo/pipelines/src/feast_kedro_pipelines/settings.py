"""Project settings."""

from kedro.framework.session.service_session import KedroServiceSession
from omegaconf.resolvers import oc

# Enable ${oc.env:...} interpolation in the config (used in catalog.yml).
CONFIG_LOADER_ARGS = {
    "custom_resolvers": {
        "oc.env": oc.env,
    },
}

# The built-in HTTP server (`kedro.server.create_http_server`) reuses a single
# service session across requests.
SESSION_CLASS = KedroServiceSession
