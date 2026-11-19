#!/bin/sh
set -eu

cd "$(CDPATH='' cd "$(dirname "$0")/.." && pwd)"

usage() {
  printf "%s\n" "Usage: sh tools/run-tests.sh list | --allow-sut one CASE | --allow-sut group AREA | --allow-sut all" >&2
  exit 64
}
allow_sut=false
if [ "${1-}" = "--allow-sut" ]; then allow_sut=true; shift; fi
case "${1-}" in
  list)
    [ "$#" -eq 1 ] || usage
    printf '%s\n' 'login-success [login] Successful login'
    exit 0 ;;
  one|group) [ "$#" -eq 2 ] || usage ;;
  all) [ "$#" -eq 1 ] || usage ;;
  *) usage ;;
esac

case "$1:${2-}" in
  'one:login-success') set -- --tests 'tests.LoginTest.successfulLoginTest' ;;
  'group:login') set -- --tests 'tests.LoginTest' ;;
  'all:') set -- ;;
  *) usage ;;
esac

if [ "$allow_sut" = false ]; then
  printf '%s\n' 'BLOCKED: approve the selected browser test before using --allow-sut.' >&2
  exit 77
fi

printf '+ gradle --offline test --rerun'
for arg in "$@"; do printf " '%s'" "$arg"; done
printf '\n'
exec gradle --offline test --rerun "$@"
