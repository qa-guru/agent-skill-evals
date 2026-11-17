#!/bin/sh
# Seeds a stale expected text into the copied LoginTest for
# evals/cases/fix-failing-stale-expectation.case. $1 = copied workdir.
set -eu
f="$1/src/test/java/tests/LoginTest.java"
grep -Fq 'New year, user1!' "$f" || {
  printf '%s\n' "BLOCKED: stale-expectation fixture no longer matches LoginTest.java" >&2
  exit 69
}
sed 's/New year, user1!/Welcome, user1!/' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
