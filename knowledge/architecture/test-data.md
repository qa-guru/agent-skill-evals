# Test data and environment

[login.html](../../login.html) checks fixed demo credentials in the browser.
It has no server or persistent account data, so no setup or cleanup is needed.

[LoginTest.java](../../src/test/java/tests/LoginTest.java) opens the fixture with
a `file:` URI and checks the English welcome message. The `?ru` variant changes
the feedback language and is not part of this test.

Do not switch to an external target or use real credentials in the fixture.
