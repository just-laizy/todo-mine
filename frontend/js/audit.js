if (!getToken()) window.location.href = "index.html";
const ACTION_META = {
    "task.created":         { label: "created a task",     color: "var(--done)" },
    "task.status_changed":  { label: "moved a task",       color: "var(--progress)" },
    "task.reviewed":        { label: "reviewed a task",    color: "var(--review)" },
    "task.deleted":         { label: "deleted a task",     color: "var(--danger)" },
    "team.created":         { label: "created a team",     color: "var(--accent)" },
    "team.member_added":    { label: "added a member",     color: "var(--progress)" },
    "team.member_removed":  { label: "removed a member",   color: "var(--danger)" },
    "user.updated":         { label: "updated a user",     color: "var(--todo)" },
};

let allEntries = [];
let limit = 25;
const userNames = new Map();

async function loadMe() {
    const me = await api("/auth/me");
    document.getElementById("me-name").textContent = me.name;
    document.getElementById("me-role").textContent = me.role;
    document.getElementById("avatar").textContent = me.name.slice(0, 2).toUpperCase();
    document.querySelectorAll("[data-roles]").forEach((l) => {
        if (!l.dataset.roles.split(",").includes(me.role)) l.remove();
    });
}

async function loadNames() {
    try {
        const users = await api("/admin/users");
        users.forEach((u) => userNames.set(u.id, u.name));
    } catch { /* ignore */ }
}

async function loadAudit() {
    allEntries = await api("/admin/audit?limit=" + limit);
    render();
}

function timeAgo(iso) {
    if (iso && !iso.endsWith("Z") && !iso.includes("+")) iso += "Z";
    const diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return "just now";
    if (diff < 3600) return Math.floor(diff / 60) + "m ago";
    if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
    return Math.floor(diff / 86400) + "d ago";
}

function render() {
    const summary = document.getElementById("audit-summary");
    const todayCount = allEntries.filter((e) => timeAgo(e.created_at).includes("m ago") || timeAgo(e.created_at) === "just now" || timeAgo(e.created_at).includes("h ago")).length;
    summary.innerHTML = "";
    [["Actions shown", allEntries.length], ["Recent (24h)", todayCount]].forEach(([label, num]) => {
        const chip = document.createElement("div");
        chip.className = "chip";
        chip.style.cursor = "default";
        chip.innerHTML = `<div class="num">${num}</div><div class="lbl">${label}</div>`;
        summary.appendChild(chip);
    });

    const term = document.getElementById("search").value.toLowerCase();
    const action = document.getElementById("filter-action").value;

    const visible = allEntries.filter((e) =>
        (!action || e.action === action) &&
        (!term || (e.details || "").toLowerCase().includes(term))
    );

    const feed = document.getElementById("audit-feed");
    feed.innerHTML = "";

    for (const entry of visible) {
        const meta = ACTION_META[entry.action] || { label: entry.action, color: "var(--text-dim)" };
        const actor = userNames.get(entry.user_id) || ("User " + entry.user_id);

        const row = document.createElement("div");
        row.className = "audit-row";

        const dot = document.createElement("div");
        dot.className = "audit-dot";
        dot.style.background = meta.color;

        const body = document.createElement("div");
        body.className = "audit-body";
        body.innerHTML =
            `<div class="audit-line"><strong>${actor}</strong> ${meta.label}` +
            (entry.details ? ` <span class="audit-detail">— ${entry.details}</span>` : "") + `</div>`;

        const time = document.createElement("div");
        time.className = "audit-time";
        time.textContent = timeAgo(entry.created_at);
        time.title = new Date(entry.created_at).toLocaleString();

        row.append(dot, body, time);
        feed.appendChild(row);
    }

    if (visible.length === 0) {
        feed.innerHTML = `<div class="audit-row"><div class="audit-body">No matching activity</div></div>`;
    }

    document.getElementById("load-more").style.display =
        allEntries.length >= limit ? "block" : "none";
}

document.getElementById("load-more").addEventListener("click", () => {
    limit += 25;
    loadAudit();
});
document.getElementById("search").addEventListener("input", render);
document.getElementById("filter-action").addEventListener("change", render);
document.getElementById("logout").addEventListener("click", () => {
    clearToken();
    window.location.href = "index.html";
});

async function boot() {
    await loadMe();
    await loadNames();
    loadAudit();
}
boot();