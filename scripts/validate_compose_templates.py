#!/usr/bin/env python3
"""Validate every Portainer template stack with Docker Compose.

The script builds a conservative environment from templates.json defaults plus
safe placeholders for required secrets. It does not start containers.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_JSON = ROOT / "templates.json"

BASE_DEFAULTS = {
    "NETWORK": "proxy",
    "PROXY_NETWORK": "proxy",
    "TRAEFIK_CERT_RESOLVER": "letsencrypt",
    "TRAEFIK_CERTRESOLVER": "letsencrypt",
    "ACME_EMAIL": "admin@example.com",
    "INTERNAL_API_TOKEN": "placeholder",
    "API_KEY_PEPPER": "placeholder",
    "APP_JWT_SECRET": "placeholder",
    "CERT_MASTER_KEY_BASE64": "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
    "REDIS_PASSWORD": "placeholder",
    "GITEA__MAILER__PASSWD": "placeholder",
}

COMMON_PLACEHOLDERS = {
    "URL": "placeholder.example.com",
    "URL_DOMAIN": "placeholder.example.com",
    "DOMAIN": "placeholder.example.com",
    "SITE_URL": "placeholder.example.com",
    "APP_DOMAIN": "placeholder.example.com",
    "POSTGRES_PASSWORD": "placeholder",
    "MYSQL_PASSWORD": "placeholder",
    "MYSQL_ROOT_PASSWORD": "placeholder",
    "RUSTFS_ACCESS_KEY": "placeholder",
    "RUSTFS_SECRET_KEY": "placeholder",
    "ECF_GATEWAY_AUTH_JWT_SECRET": "placeholder",
    "ECF_GATEWAY_MASTER_KEY": "nP7nU9LQaVWL7LMGCB6I-xiOhRz57EuKAzyouImEv_E=",
}


def build_env(template: dict[str, object]) -> dict[str, str]:
    env = os.environ.copy()
    env.update(BASE_DEFAULTS)
    env.setdefault("COMPOSE_PROJECT_NAME", f"tpl{template['id']}")

    for item in template.get("env", []):
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            continue
        default = item.get("default")
        env[name] = str(default if default not in (None, "") else BASE_DEFAULTS.get(name, "placeholder"))

    for key, value in COMMON_PLACEHOLDERS.items():
        env.setdefault(key, value)

    return env


def main() -> int:
    data = json.loads(TEMPLATES_JSON.read_text(encoding="utf-8"))
    failures: list[tuple[int, str, str, str]] = []
    checked = 0

    for template in data.get("templates", []):
        repository = template.get("repository") or {}
        if not isinstance(repository, dict):
            continue
        stackfile = repository.get("stackfile")
        if not isinstance(stackfile, str) or not stackfile.endswith("docker-compose.yml"):
            continue
        stack_path = ROOT / stackfile
        if not stack_path.exists():
            continue

        checked += 1
        completed = subprocess.run(
            ["docker", "compose", "-f", stackfile, "config", "--quiet"],
            cwd=ROOT,
            env=build_env(template),
            text=True,
            capture_output=True,
            timeout=30,
        )
        if completed.returncode:
            output = (completed.stderr or completed.stdout).strip()
            failures.append((template["id"], template.get("title", "<untitled>"), stackfile, output))

    if failures:
        print(f"Docker Compose validation failed for {len(failures)} of {checked} templates:")
        for template_id, title, stackfile, output in failures:
            print(f"- [{template_id}] {title} ({stackfile})")
            for line in output.splitlines()[:8]:
                print(f"  {line}")
        return 1

    print(f"Docker Compose validation passed for {checked} templates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
