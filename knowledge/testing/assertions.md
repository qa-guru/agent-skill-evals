# Assertions

Canonical: checks stay inline in test bodies against the elements/state the code exposes.

The canonical example is [LoginTest.successfulLoginTest](../../src/test/java/tests/LoginTest.java):
inline UI actions followed by exactly one terminal `shouldHave(text(...))` assertion.
Use its current locator and the SUT's confirmed expected text, not a duplicated snapshot.

## Do
- Assert in the test; reach page state through the exposed elements/methods, not new locators.
- Reuse the framework's retrying conditions; the expected texts come from the test data source.
- Mirror the canonical test verbatim: same chain form and check count — one scenario asserts only its expected outcome.

## Don't
- No weakened assertions, arbitrary sleeps or expected-text edits to obtain a green run; aligning an expected value with the SUT's confirmed current contract is a stale-expectation fix, not a weakening.
- No redundant checks: a retrying assertion already waits for the element state; never prepend visibility checks to a text/state assertion.
- No assertion padding: assert exactly the scenario's expected outcome — no extra visibility checks, no re-verifying page or form state after the terminal assertion.
