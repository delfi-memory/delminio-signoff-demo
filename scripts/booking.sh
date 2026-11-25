#!/usr/bin/env bash
set -euo pipefail
number=${1:-}
[[ $# == 1 && $number =~ ^[0-9]{1,6}$ ]] || { echo 'Usage: scripts/booking.sh NUMBER' >&2; exit 2; }
exec psql booking-prod -XA -P footer=off -F ' | ' -c "SELECT number, status, total_cents, refunded_cents FROM bookings WHERE number = $number"
