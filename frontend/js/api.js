const API = "";

function getToken()  { return localStorage.getItem("token"); }
function setToken(t) { localStorage.setItem("token", t); }
function clearToken(){ localStorage.removeItem("token"); }

async function api(path, options = {}) {
    const headers = options.headers || {};
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
    if (options.body && !(options.body instanceof URLSearchParams)) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(API + path, { ...options, headers });

    if (response.status === 401) {
        clearToken();
        window.location.href = "index.html";
        return null;
    }
    if (response.status === 204) return null;

    const data = await response.json().catch(() => null);
    if (!response.ok) {
        const detail = data && data.detail;
        throw new Error(typeof detail === "string" ? detail : "Request failed (" + response.status + ")");
    }
    return data;
}