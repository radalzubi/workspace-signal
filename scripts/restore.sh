#!/bin/sh
set -eu

database_dump="${1:?database dump path is required}"
media_archive="${2:?media archive path is required}"
media_root="${MEDIA_ROOT:-./media/generated}"

test -f "$database_dump"
test -f "$media_archive"
mkdir -p "$media_root"
pg_restore --clean --if-exists --no-owner --dbname="${DATABASE_URL:?DATABASE_URL is required}" "$database_dump"
tar -xzf "$media_archive" -C "$media_root"
printf '%s\n' "Restore complete; run migration and application validation next."

