// let mode = "signin";

// const tabSignin = document.getElementById("tab-signin");
// const tabSignup = document.getElementById("tab-signup");
// const nameField = document.getElementById("name-field");
// const submitBtn = document.getElementById("submit");
// const errorEl   = document.getElementById("error");

// function setMode(next) {
//     mode = next;
//     tabSignin.classList.toggle("active", mode === "signin");
//     tabSignup.classList.toggle("active", mode === "signup");
//     nameField.classList.toggle("hidden", mode === "signin");
//     submitBtn.textContent = mode === "signin" ? "Sign in" : "Create account";
//     errorEl.textContent = "";
// }

// tabSignin.addEventListener("click", () => setMode("signin"));
// tabSignup.addEventListener("click", () => setMode("signup"));

// async function login(email, password) {
//     const body = new URLSearchParams({ username: email, password: password });
//     const data = await api("/auth/login", { method: "POST", body });
//     setToken(data.access_token);
//     window.location.href = "dashboard.html";
// }

// document.getElementById("auth-form").addEventListener("submit", async (event) => {
//     event.preventDefault();
//     errorEl.textContent = "";
//     const email = document.getElementById("email").value;
//     const password = document.getElementById("password").value;

//     try {
//         if (mode === "signup") {
//             const name = document.getElementById("name").value;
//             await api("/auth/register", {
//                 method: "POST",
//                 body: JSON.stringify({ name, email, password }),
//             });
//         }
//         await login(email, password);
//     } catch (err) {
//         errorEl.textContent = err.message;
//     }
// });
let mode = "signin"; // "signin" (existing user) or "signup" (register)
let step = "request"; // "request" or "verify"
let userEmail = "";

// DOM Elements
const tabSignin = document.getElementById("tab-signin");
const tabSignup = document.getElementById("tab-signup");
const authForm = document.getElementById("auth-form");
const nameField = document.getElementById("name-field");
const nameInput = document.getElementById("name");
const emailField = document.getElementById("email-field");
const emailInput = document.getElementById("email");
const otpField = document.getElementById("otp-field");
const otpInput = document.getElementById("password");
const submitBtn = document.getElementById("submit");
const errorEl = document.getElementById("error");

// Render the form for the current mode + step. Does NOT touch the error line
// so a message set by the submit handler survives the post-request re-render.
function render() {
  tabSignin.classList.toggle("active", mode === "signin");
  tabSignup.classList.toggle("active", mode === "signup");

  if (step === "request") {
    nameField.classList.toggle("hidden", mode === "signin"); // name only for signup
    emailField.classList.remove("hidden");
    otpField.classList.add("hidden");
    submitBtn.textContent = mode === "signup" ? "Create account & Send OTP" : "Send OTP Code";
  } else {
    nameField.classList.add("hidden");
    emailField.classList.add("hidden");
    otpField.classList.remove("hidden");
    submitBtn.textContent = "Verify & Sign In";
  }
}

function setMode(nextMode) {
  mode = nextMode;
  step = "request";
  errorEl.textContent = "";
  render();
}

function setStep(nextStep) {
  step = nextStep;
  errorEl.textContent = "";
  render();
}

tabSignin.addEventListener("click", () => setMode("signin"));
tabSignup.addEventListener("click", () => setMode("signup"));

// Initial setup
render();

// Sign in: request OTP for an existing account
async function requestOTP(email) {
  await api("/auth/request-otp", {
    method: "POST",
    body: JSON.stringify({ email: email }),
  });
  userEmail = email;
  setStep("verify");
}

// Sign up: create the account, which also sends an OTP
async function registerUser(name, email) {
  await api("/auth/register", {
    method: "POST",
    body: JSON.stringify({ name: name, email: email }),
  });
  userEmail = email;
  setStep("verify");
}

// Shared step 2: verify OTP and save JWT token
async function verifyOTP(email, code) {
  const data = await api("/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({ email: email, code: code }),
  });

  setToken(data.access_token);
  window.location.href = "dashboard.html";
}

// Form Submit Event Handler
authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.textContent = "";
  submitBtn.disabled = true;

  try {
    if (step === "request") {
      const email = emailInput.value.trim();
      if (!email) throw new Error("Please enter your email.");

      if (mode === "signup") {
        const name = nameInput.value.trim();
        if (!name) throw new Error("Please enter your name.");
        submitBtn.textContent = "Creating account...";
        await registerUser(name, email);
      } else {
        submitBtn.textContent = "Sending...";
        await requestOTP(email);
      }
    } else if (step === "verify") {
      const code = otpInput.value.trim();
      if (!code) throw new Error("Please enter the 6-digit OTP code.");

      submitBtn.textContent = "Verifying...";
      await verifyOTP(userEmail, code);
    }
  } catch (err) {
    errorEl.textContent = err.message || "An error occurred";
  } finally {
    submitBtn.disabled = false;
    render(); // restore the correct button label for the current step
  }
});