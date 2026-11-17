#!/bin/sh
# Seeds a stale expected text into the copied LoginTest for
# evals/cases/fix-failing-stale-expectation.case. $1 = copied workdir.
set -eu
f="$1/src/test/java/tests/LoginTest.java"
grep -Eq 'authorized-banner.*text\("' "$f" || {
  printf '%s\n' "BLOCKED: no text() assertion on authorized-banner in LoginTest.java" >&2
  exit 69
}
sed '/authorized-banner/ s/text("[^"]*")/text("Welcome, user1!")/' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
