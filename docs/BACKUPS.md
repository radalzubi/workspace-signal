# Backup and restore

## Database

Run `scripts/backup.sh` from an environment with `DATABASE_URL` or explicit
Postgres connection variables. It creates a compressed custom-format dump and a
media archive in a timestamped directory. Copy backups to encrypted offsite
storage with lifecycle retention (for example: 7 daily, 4 weekly, 6 monthly).

Restore into a new empty database first:

```bash
scripts/restore.sh backups/20260814T120000Z/database.dump backups/20260814T120000Z/media.tar.gz
```

Validate row counts, migrations, media checksums, login, health, and a dry-run
publication. Never test restoration against the only production database.

For production revenue dependence, prefer managed PostgreSQL point-in-time
recovery plus these logical dumps. Back up the OAuth encryption master key in a
separate secret system; database backups alone cannot decrypt credentials.

