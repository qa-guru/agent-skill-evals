# Version sources

- [build.gradle](../../build.gradle) declares Java 21 and the test dependencies.
- [tools/versions.sh](../../tools/versions.sh) checks `java` and `javac` 21, Gradle 9.6.0, and the presence of Git. There is no Gradle wrapper.
- The [CI setup action](../../.github/actions/test-env/action.yml) installs the same Java and Gradle versions and runs that check.

A run with different pins is a compatibility check, not a pass on the lesson's toolchain.
