if (!getToken()) window.location.href = "index.html";

const ROLE_LABELS = { user: "User", manager: "Manager", superadmin: "Superadmin" };

let me = null;
let allUsers = [];
let teams = [];
let editingId = null;

const toastEl = document.getElementById("toast");
function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    setTimeout(() => toastEl.classList.remove("show"), 3000);
}

function teamName(teamId) {
    const team = teams.find((t) => t.id === teamId);
    return team ? team.name : (teamId ? "Team " + teamId : "No team");
}

async function loadMe() {
    me = await api("/auth/me");
    document.getElementById("me-name").textContent = me.name;
    document.getElementById("me-role").textContent = me.role;
    document.getElementById("avatar").textContent = me.name.slice(0, 2).toUpperCase();
    document.querySelectorAll("[data-roles]").forEach((l) => {
        if (!l.dataset.roles.split(",").includes(me.role)) l.remove();
    });
    loadUsers();
}

async function loadUsers() {
    if (me.role === "superadmin") {
        try {
            teams = await api("/admin/teams");
        } catch { teams = []; }
        allUsers = await api("/admin/users");
    } else {
        allUsers = await api("/users/assignable");
    }
    render();
}

function visibleUsers() {
    const term = document.getElementById("search").value.toLowerCase();
    const role = document.getElementById("filter-role").value;

    return allUsers.filter((u) =>
        (u.name.toLowerCase().includes(term) || u.email.toLowerCase().includes(term)) &&
        (!role || u.role === role)
    );
}

function renderSummary() {
    const box = document.getElementById("user-summary");
    box.innerHTML = "";

    const counts = [
        { label: "Total",       num: allUsers.length },
        { label: "Users",       num: allUsers.filter(u => u.role === "user").length },
        { label: "Managers",    num: allUsers.filter(u => u.role === "manager").length },
        { label: "No team",     num: allUsers.filter(u => !u.team_id).length },
    ];

    for (const c of counts) {
        const el = document.createElement("div");
        el.className = "chip";
        el.style.cursor = "default";
        el.innerHTML = `<div class="num">${c.num}</div><div class="lbl">${c.label}</div>`;
        box.appendChild(el);
    }
}

function render() {
    renderSummary();

    const list = document.getElementById("user-list");
    list.innerHTML = "";

    for (const user of visibleUsers()) {
        const row = document.createElement("div");
        row.className = "task-row";

        const avatar = document.createElement("div");
        avatar.className = "avatar avatar-sm";
        avatar.textContent = user.name.slice(0, 2).toUpperCase();

        const info = document.createElement("div");
        info.className = "u-info";
        info.innerHTML = `<div class="u-name">${user.name}</div><div class="u-email">${user.email}</div>`;

        const role = document.createElement("span");
        role.className = "pill role-pill";
        role.dataset.role = user.role;
        role.textContent = ROLE_LABELS[user.role] || user.role;

        const team = document.createElement("span");
        team.className = "t-status";
        team.textContent = teamName(user.team_id);

        row.append(avatar, info, role, team);

        if (me.role === "superadmin") {
            row.addEventListener("click", () => openEdit(user));
        } else {
            row.style.cursor = "default";
        }

        list.appendChild(row);
    }

    if (list.children.length === 0) {
        list.innerHTML = `<div class="task-row"><span class="t-title">No users match</span></div>`;
    }
}

const editModal = document.getElementById("edit-backdrop");
const eError = document.getElementById("e-error");

function openEdit(user) {
    editingId = user.id;
    eError.textContent = "";
    document.getElementById("e-title").textContent = user.name;
    document.getElementById("e-sub").textContent = user.email;
    document.getElementById("e-role").value = user.role;
    document.getElementById("e-status").value = user.status || "active";

    const teamSelect = document.getElementById("e-team");
    teamSelect.innerHTML = `<option value="">No team</option>`;
    for (const team of teams) {
        const option = document.createElement("option");
        option.value = team.id;
        option.textContent = team.name;
        teamSelect.appendChild(option);
    }
    teamSelect.value = user.team_id || "";

    editModal.classList.remove("hidden");
}

function closeEdit() {
    editModal.classList.add("hidden");
    editingId = null;
}

document.getElementById("e-cancel").addEventListener("click", closeEdit);
editModal.addEventListener("click", (e) => { if (e.target === editModal) closeEdit(); });

document.getElementById("e-save").addEventListener("click", async () => {
    eError.textContent = "";
    const teamValue = document.getElementById("e-team").value;

    const payload = {
        role:   document.getElementById("e-role").value,
        status: document.getElementById("e-status").value,
    };
    if (teamValue) payload.team_id = Number(teamValue);

    try {
        await api("/admin/users/" + editingId, {
            method: "PATCH",
            body: JSON.stringify(payload),
        });
        closeEdit();
        toast("User updated");
        loadUsers();
    } catch (err) {
        eError.textContent = err.message;
    }
});

document.getElementById("search").addEventListener("input", render);
document.getElementById("filter-role").addEventListener("change", render);
document.getElementById("logout").addEventListener("click", () => {
    clearToken();
    window.location.href = "index.html";
});

loadMe();