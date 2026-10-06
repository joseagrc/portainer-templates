# Traefik Multi-Instance Template Standard

This repository assumes a single shared Traefik reverse proxy and one external
Docker network, normally named `proxy`.

Every template that exposes HTTP traffic should follow these rules so the same
template can be deployed multiple times on the same Docker host.

## Required Variables

- `COMPOSE_PROJECT_NAME`: unique stack instance name. Examples:
  `n8n-client-a`, `n8n-client-b`, `gitea-lab`.
- `NETWORK`: external Traefik network. Default: `proxy`.
- `TRAEFIK_CERT_RESOLVER`: certificate resolver configured in Traefik.
- A public host variable per exposed app, such as `URL`, `URL_DOMAIN`,
  `DOMAIN`, `APP_DOMAIN`, `PORTAL_DOMAIN` or `ENGINE_DOMAIN`.

## Router, Service, and Middleware Names

Traefik object names must include `COMPOSE_PROJECT_NAME`.

Good:

```yaml
labels:
  - traefik.enable=true
  - traefik.docker.network=${NETWORK:-proxy}
  - traefik.http.routers.${COMPOSE_PROJECT_NAME:-myapp}.rule=Host(`${URL}`)
  - traefik.http.routers.${COMPOSE_PROJECT_NAME:-myapp}.entrypoints=websecure
  - traefik.http.routers.${COMPOSE_PROJECT_NAME:-myapp}.tls=true
  - traefik.http.routers.${COMPOSE_PROJECT_NAME:-myapp}.tls.certresolver=${TRAEFIK_CERT_RESOLVER:-letsencrypt}
  - traefik.http.services.${COMPOSE_PROJECT_NAME:-myapp}.loadbalancer.server.port=8080
```

Avoid:

```yaml
labels:
  - traefik.http.routers.myapp.rule=Host(`${URL}`)
  - traefik.http.services.myapp.loadbalancer.server.port=8080
```

Static router or service names collide when the same template is installed
twice.

## Networks

Use an internal network for databases, caches and workers, and attach only the
public HTTP service to the external proxy network.

```yaml
networks:
  backend:
    internal: true
  proxy:
    external: true
    name: ${NETWORK:-proxy}
```

## Ports

Do not publish application HTTP ports when Traefik is responsible for ingress.
Prefer `expose` or no host port at all. Publish ports only for protocols Traefik
does not handle in the template, such as WireGuard UDP or SSH, and make those
ports configurable.

## Container Names

Avoid hard-coded `container_name`. If a template truly needs one, derive it from
`COMPOSE_PROJECT_NAME`.

```yaml
container_name: ${COMPOSE_PROJECT_NAME:-myapp}-app
```

## Volume Names

Named volumes are normally scoped by Compose project automatically. Use fixed
external volume names only when the template is intentionally attaching to
pre-existing data.

