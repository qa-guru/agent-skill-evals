#!/bin/sh
# Heals LoginTest.java's contract points from the SUT (login.html):
# the data-testid selectors, the valid credentials and the expected
# welcome text. Anchors are semantic — input autocomplete, type=submit,
# and the getElementById(...).textContent = ...welcome binding — so SUT
# renames are followed; anything the SUT no longer provides fails loudly.
set -eu

cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd)"

sut=login.html
test=src/test/java/tests/LoginTest.java

# attr NAME FRAGMENT — attribute value on the SUT line containing FRAGMENT.
attr() {
  grep -F "$2" "$sut" | grep -oE "$1=\"[^\"]+\"" | head -1 | cut -d'"' -f2
}

# The welcome element is identified through the JS binding, not its id:
# whichever element receives ".textContent = ...welcome" is the banner.
wid=$(grep -A1 'getElementById.*textContent' "$sut" | grep -B1 welcome \
      | grep -oE "getElementById\('[^']+'" | head -1 | cut -d"'" -f2)

tid_login=$(attr data-testid 'autocomplete="username"')
tid_pass=$(attr data-testid 'type="password"')
tid_submit=$(attr data-testid 'type="submit"')
tid_banner=$(attr data-testid "id=\"$wid\"")

user=$(grep -oE "login !== '[^']+'" "$sut" | head -1 | cut -d"'" -f2)
pass=$(grep -oE "password !== '[^']+'" "$sut" | head -1 | cut -d"'" -f2)
tmpl=$(sed -n "s/.*en: *{ *welcome: *'\([^']*\)'.*/\1/p" "$sut" | head -1)

missing=""
for pair in "tid_login:$tid_login" "tid_pass:$tid_pass" "tid_submit:$tid_submit" \
            "tid_banner:$tid_banner" "user:$user" "pass:$pass" "tmpl:$tmpl"; do
  [ -n "${pair#*:}" ] || missing="$missing ${pair%%:*}"
done
[ -z "$missing" ] || {
  printf '%s\n' "::error::cannot derive contract from $sut:$missing" >&2
  exit 1
}

# DOM getText collapses whitespace runs and trims — the assertion literal
# must equal the rendered text, not the raw template.
expected=$(printf '%s' "$tmpl" | sed "s/{[A-Za-z_][A-Za-z_]*}/$user/g" \
           | tr -s '[:space:]' ' ' | sed 's/^ //; s/ $//')

esc() { printf '%s' "$1" | sed 's/[\\&]/\\&/g'; }

awk -v tl="$tid_login" -v tp="$tid_pass" -v ts="$tid_submit" -v tb="$tid_banner" \
    -v u="$(esc "$user")" -v p="$(esc "$pass")" -v e="$(esc "$expected")" '
  /setValue\("[^"]*"\)/ {
    n++
    sub(/data-testid=[^]]*/, "data-testid=" (n == 1 ? tl : tp))
    sub(/setValue\("[^"]*"\)/, "setValue(\"" (n == 1 ? u : p) "\")")
  }
  /\.click\(\)/ { sub(/data-testid=[^]]*/, "data-testid=" ts) }
  /shouldHave\(text\("[^"]*"\)\)/ {
    sub(/data-testid=[^]]*/, "data-testid=" tb)
    sub(/text\("[^"]*"\)/, "text(\"" e "\")")
  }
  { print }
' "$test" > "$test.tmp" && mv "$test.tmp" "$test"
