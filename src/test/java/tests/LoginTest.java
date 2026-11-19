package tests;

import java.nio.file.Path;

import org.junit.jupiter.api.Test;

import static com.codeborne.selenide.Condition.text;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.open;

class LoginTest {
    @Test
    void successfulLoginTest() {
        open(Path.of("login.html").toAbsolutePath().toUri().toString());
        $("[data-testid=login-input]").setValue("user1");
        $("[data-testid=password-input]").setValue("password1");
        $("[data-testid=submit-button]").click();
        $("[data-testid=welcome-banner]").shouldHave(text("Safe travels, user1!"));
    }
}
