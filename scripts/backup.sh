#!/bin/sh
set -eu

backup_root="${BACKUP_ROOT:-./backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${backup_root}/${timestamp}"
media_root="${MEDIA_ROOT:-./media/generated}"
mkdir -p "$target"

pg_dump --format=custom --no-owner --file="${target}/database.dump" "${DATABASE_URL:?DATABASE_URL is required}"
tar -czf "${target}/media.tar.gz" -C "$media_root" .
printf '%s\n' "Backup created at ${target}"

