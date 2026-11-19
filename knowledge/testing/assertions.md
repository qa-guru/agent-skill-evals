# Assertions

[LoginTest.successfulLoginTest](../../src/test/java/tests/LoginTest.java) submits
the form and ends with one `shouldHave(text(...))` assertion on the welcome banner.
Read the current fixture and test before changing a selector or expectation.

- Keep the full expected greeting. `text(...)` matches a substring, so replacing it with just the username would weaken the check.
- Keep the retrying assertion and its position. Do not add a sleep, a separate visibility check, or checks after the expected outcome.
