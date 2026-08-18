# Honrapp restoration stack

Before deploying this template, place the restored files on the Docker host:

- `/home/honrapp/.docker/honrapp/webapp/publish`: published .NET application files.
- `/home/honrapp/.docker/honrapp/mssql/honrapp.bak`: verified SQL Server backup.

The `mssql` directory must be traversable by the container (`0755`) and the
backup readable (`0644`). The enclosing `/home/honrapp` directory can remain
private (`0700`).

The one-shot `restore` service creates the `honrapp` database only when it does
not exist, then runs `DBCC CHECKDB`. Redeployments never overwrite an existing
database. The database is reachable only on the private Compose network; the
web application is published by the existing Traefik `proxy` network.

The source server's nginx-proxy and Portainer backups are intentionally not part
of this stack because server1 already provides those roles with Traefik and its
current Portainer installation.
