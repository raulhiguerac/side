import os

# Read at import time by api/deps (auth, db) and core/config/settings; collection aborts without them.
os.environ.setdefault("KC_JWKS_URL", "http://keycloak.test/realms/test/protocol/openid-connect/certs")
os.environ.setdefault("KC_ISSUER", "http://keycloak.test/realms/test")
os.environ.setdefault("OIDC_AUDIENCE", "test-audience")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("FRONT_BASE_URL", "http://localhost:8080")
