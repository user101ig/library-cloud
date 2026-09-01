# Keycloak μαζί με realm και custom theme.
FROM quay.io/keycloak/keycloak:26.7.1

COPY --chown=keycloak:keycloak import /opt/keycloak/data/import
COPY --chown=keycloak:keycloak themes /opt/keycloak/themes
