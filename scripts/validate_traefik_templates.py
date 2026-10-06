#!/usr/bin/env python3
"""Static checks for Portainer templates that are exposed through Traefik."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STACKS = ROOT / "stacks"

TRAEFIK_OBJECT_RE = re.compile(
    r"traefik\.http\.(?:routers|services|middlewares)\.([^.=:\s]+)"
)

ALLOW_STATIC_OBJECTS = {
    # Shared middlewares that are expected to be provided by Traefik file config.
    "security@file",
    "hsts@file",
    "compression_https@file",
    "rate-limit-strict@file",
}

ALLOW_HOST_PORT_TEMPLATES = {
    # Non-HTTP or special-purpose templates where host ports are expected.
    "wireguard",
    "pi-hole",
    "gitlab-ce",
    "gitea",
    "forgejo",
    "gnuhealth",
    "macos",
    "windows",
    "zabbix",
    "wazuh",
    "openldap",
    "haproxy",
    "nextcloudaio",
}


def iter_compose_files() -> list[Path]:
    return sorted(STACKS.glob("*/docker-compose.yml"))


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def validate_file(path: Path) -> list[str]:
    rel = path.relative_to(ROOT)
    template_name = path.parent.name
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if "traefik.enable" in text:
        if not re.search(r"traefik\.docker\.network[:=]\s*\$\{(?:PROXY_)?NETWORK", text):
            errors.append(f"{rel}: Traefik-enabled template should set traefik.docker.network from NETWORK.")

        for match in TRAEFIK_OBJECT_RE.finditer(text):
            object_name = match.group(1)
            if object_name in ALLOW_STATIC_OBJECTS:
                continue
            if "${COMPOSE_PROJECT_NAME" not in object_name:
                errors.append(
                    f"{rel}:{line_number(text, match.start())}: Traefik object '{object_name}' "
                    "must include ${COMPOSE_PROJECT_NAME...} to support multiple instances."
                )

        if "ports:" in text and template_name not in ALLOW_HOST_PORT_TEMPLATES:
            errors.append(
                f"{rel}: Traefik-enabled HTTP templates should not publish host ports; "
                "use Traefik labels instead or add a justified exception."
            )

    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("container_name:"):
            continue
        if "${COMPOSE_PROJECT_NAME" not in stripped:
            errors.append(f"{rel}:{idx}: container_name must be omitted or derived from COMPOSE_PROJECT_NAME.")

    return errors


def main() -> int:
    errors: list[str] = []
    for compose_file in iter_compose_files():
        errors.extend(validate_file(compose_file))

    if errors:
        print("Traefik template validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Traefik template validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
