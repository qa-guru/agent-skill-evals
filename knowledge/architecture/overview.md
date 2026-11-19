# Architecture

- [login.html](../../login.html) is a local HTML/JavaScript fixture. The test opens it with a `file:` URI.
- [LoginTest.java](../../src/test/java/tests/LoginTest.java) contains the only automated scenario: successful login. The selectors and [assertion](../testing/assertions.md) stay inline; a Page Object would add indirection for this one test.
- [build.gradle](../../build.gradle) configures Java 21, JUnit and Selenide. [Local commands](../testing/run-tests.md) compile or run the test.
- [ai-pipeline.yml](../../.github/workflows/ai-pipeline.yml) runs the full suite, reproduces failed JUnit cases, and commits a test fix to `main` only after the full suite passes with the fix.
