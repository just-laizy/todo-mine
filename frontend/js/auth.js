let mode = "signin";

const tabSignin = document.getElementById("tab-signin");
const tabSignup = document.getElementById("tab-signup");
const nameField = document.getElementById("name-field");
const submitBtn = document.getElementById("submit");
const errorEl   = document.getElementById("error");

function setMode(next) {
    mode = next;
    tabSignin.classList.toggle("active", mode === "signin");
    tabSignup.classList.toggle("active", mode === "signup");
    nameField.classList.toggle("hidden", mode === "signin");
    submitBtn.textContent = mode === "signin" ? "Sign in" : "Create account";
    errorEl.textContent = "";
}

tabSignin.addEventListener("click", () => setMode("signin"));
tabSignup.addEventListener("click", () => setMode("signup"));

async function login(email, password) {
    const body = new URLSearchParams({ username: email, password: password });
    const data = await api("/auth/login", { method: "POST", body });
    setToken(data.access_token);
    window.location.href = "dashboard.html";
}

document.getElementById("auth-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.textContent = "";
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        if (mode === "signup") {
            const name = document.getElementById("name").value;
            await api("/auth/register", {
                method: "POST",
                body: JSON.stringify({ name, email, password }),
            });
        }
        await login(email, password);
    } catch (err) {
        errorEl.textContent = err.message;
    }
});