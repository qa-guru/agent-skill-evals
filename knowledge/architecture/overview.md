# Architecture

- [login.html](../../login.html) is a local HTML/JavaScript fixture. The test opens it with a `file:` URI.
- [LoginTest.java](../../src/test/java/tests/LoginTest.java) contains the only automated scenario: successful login. The selectors and [assertion](../testing/assertions.md) stay inline; a Page Object would add indirection for this one test.
- [build.gradle](../../build.gradle) configures Java 21, JUnit and Selenide. [Local commands](../testing/run-tests.md) compile or run the test.
- [ai-pipeline.yml](../../.github/workflows/ai-pipeline.yml) runs the test, asks the agent for a candidate on an eligible UI failure, and independently verifies the candidate before publishing a patch.
