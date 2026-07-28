if (!getToken()) window.location.href = "index.html";

let teams = [];
let users = [];
let openTeamId = null;

const toastEl = document.getElementById("toast");
function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    setTimeout(() => toastEl.classList.remove("show"), 3000);
}

function userById(id) { return users.find((u) => u.id === id); }
function membersOf(teamId) { return users.filter((u) => u.team_id === teamId); }

async function loadMe() {
    const me = await api("/auth/me");
    document.getElementById("me-name").textContent = me.name;
    document.getElementById("me-role").textContent = me.role;
    document.getElementById("avatar").textContent = me.name.slice(0, 2).toUpperCase();
    document.querySelectorAll("[data-roles]").forEach((l) => {
        if (!l.dataset.roles.split(",").includes(me.role)) l.remove();
    });
}

async function loadData() {
    teams = await api("/admin/teams");
    users = await api("/admin/users");
    render();
    loadPerformance();
}

function render() {
    const summary = document.getElementById("team-summary");
    summary.innerHTML = "";
    const stats = [
        ["Teams", teams.length],
        ["Users", users.length],
        ["Unassigned", users.filter((u) => !u.team_id && u.role !== "superadmin").length],
    ];
    for (const [label, num] of stats) {
        const chip = document.createElement("div");
        chip.className = "chip";
        chip.style.cursor = "default";
        chip.innerHTML = `<div class="num">${num}</div><div class="lbl">${label}</div>`;
        summary.appendChild(chip);
    }

    const grid = document.getElementById("team-grid");
    grid.innerHTML = "";

        const TEAM_COLORS = ["var(--todo)", "var(--progress)", "var(--review)", "var(--done)", "var(--cat-ui_ux)"];

    for (const team of teams) {
        const members = membersOf(team.id);
        const manager = userById(team.manager_id);

        const card = document.createElement("div");
        card.className = "team-card";
        card.style.setProperty("--accent-team", TEAM_COLORS[team.id % TEAM_COLORS.length]);

        const accent = document.createElement("div");
        accent.className = "tc-accent";

        const name = document.createElement("h3");
        name.textContent = team.name;

        const mgr = document.createElement("div");
        mgr.className = "tc-manager";
        mgr.textContent = "Manager: " + (manager ? manager.name : "—");

        const avatars = document.createElement("div");
        avatars.className = "tc-avatars";
        members.slice(0, 5).forEach((m) => {
            const av = document.createElement("div");
            av.className = "tc-avatar";
            av.textContent = m.name.slice(0, 2).toUpperCase();
            av.title = m.name;
            avatars.appendChild(av);
        });
        if (members.length > 5) {
            const more = document.createElement("div");
            more.className = "tc-avatar tc-more";
            more.textContent = "+" + (members.length - 5);
            avatars.appendChild(more);
        }

        const footer = document.createElement("div");
        footer.className = "tc-footer";
        footer.innerHTML = `<span>${members.length} member${members.length === 1 ? "" : "s"}</span><span>View →</span>`;

        card.append(accent, name, mgr, avatars, footer);
        card.addEventListener("click", () => openTeam(team));
        grid.appendChild(card);
    }
}

const detail = document.getElementById("detail-backdrop");
const tError = document.getElementById("t-error");
const TEAM_COLORS = ["var(--todo)", "var(--progress)", "var(--review)", "var(--done)", "var(--cat-ui_ux)"];

async function openTeam(team) {
    openTeamId = team.id;
    tError.textContent = "";
    const manager = userById(team.manager_id);
    document.getElementById("t-name").textContent = team.name;
    document.getElementById("t-manager").textContent =
        "Managed by " + (manager ? manager.name : "—");
    document.getElementById("t-accent").style.background =
        TEAM_COLORS[team.id % TEAM_COLORS.length];

    let stats = [];
    try {
        stats = await api("/stats/team/" + team.id);
    } catch { stats = []; }

    const statById = new Map(stats.map((s) => [s.user_id, s]));
    const openOf = (s) => s ? ((s.counts.todo || 0) + (s.counts.in_progress || 0) + (s.counts.pending_review || 0)) : 0;

    const totalMembers = membersOf(team.id).length;
    const totalOpen = stats.reduce((sum, s) => sum + openOf(s), 0);
    const totalOverdue = stats.reduce((sum, s) => sum + (s.overdue || 0), 0);
    const totalDone = stats.reduce((sum, s) => sum + (s.counts.done || 0), 0);

    const tiles = document.getElementById("t-stats");
    tiles.innerHTML = "";
    [
        ["Members", totalMembers],
        ["Open tasks", totalOpen],
        ["Overdue", totalOverdue],
        ["Completed", totalDone],
    ].forEach(([label, num]) => {
        const card = document.createElement("div");
        card.className = "stat-card";
        card.innerHTML = `<div class="num">${num}</div><div class="lbl">${label}</div>`;
        tiles.appendChild(card);
    });

    const box = document.getElementById("t-members");
    box.innerHTML = "";
    const maxOpen = Math.max(1, ...membersOf(team.id).map((m) => openOf(statById.get(m.id))));

        for (const member of membersOf(team.id)) {
        const s = statById.get(member.id);
        const open = openOf(s);
        const overdue = s ? (s.overdue || 0) : 0;
        const done = s ? (s.counts.done || 0) : 0;

        const row = document.createElement("div");
        row.className = "member-row";

        const avatar = document.createElement("div");
        avatar.className = "m-avatar";
        avatar.textContent = member.name.slice(0, 2).toUpperCase();

        const info = document.createElement("div");
        info.className = "m-info";
        const roleTag = member.id === team.manager_id ? " · manager" : "";
        info.innerHTML =
            `<div class="m-name">${member.name}${roleTag}</div>` +
            `<div class="m-stats">${open} open · ${done} done` +
            (overdue ? ` · <span style="color:var(--danger)">${overdue} overdue</span>` : "") + `</div>`;

        row.append(avatar, info);

        if (member.id !== team.manager_id) {
            const del = document.createElement("button");
            del.className = "icon-btn";
            del.textContent = "✕";
            del.addEventListener("click", () => removeMember(team.id, member.id));
            row.appendChild(del);
        }

        box.appendChild(row);
    }

    const select = document.getElementById("t-add-select");
    select.innerHTML = "";
    const addable = users.filter((u) => u.team_id !== team.id && u.role !== "superadmin");
    for (const user of addable) {
        const option = document.createElement("option");
        option.value = user.id;
        option.textContent = user.name + (user.team_id ? " (from another team)" : "");
        select.appendChild(option);
    }

    detail.classList.remove("hidden");
}
async function removeMember(teamId, userId) {
    try {
        await api(`/teams/${teamId}/members/${userId}`, { method: "DELETE" });
        toast("Member removed");
        await loadData();
        openTeam(teams.find((t) => t.id === teamId));
    } catch (err) { tError.textContent = err.message; }
}

document.getElementById("t-add-btn").addEventListener("click", async () => {
    const userId = Number(document.getElementById("t-add-select").value);
    if (!userId) return;
    try {
        await api(`/teams/${openTeamId}/members`, {
            method: "POST",
            body: JSON.stringify({ user_id: userId }),
        });
        toast("Member added");
        await loadData();
        openTeam(teams.find((t) => t.id === openTeamId));
    } catch (err) { tError.textContent = err.message; }
});

document.getElementById("detail-close").addEventListener("click", () => detail.classList.add("hidden"));
detail.addEventListener("click", (e) => { if (e.target === detail) detail.classList.add("hidden"); });

const createModal = document.getElementById("create-backdrop");
const cError = document.getElementById("c-error");

document.getElementById("new-team").addEventListener("click", () => {
    document.getElementById("c-name").value = "";
    cError.textContent = "";
    createModal.classList.remove("hidden");
});
document.getElementById("c-cancel").addEventListener("click", () => createModal.classList.add("hidden"));
createModal.addEventListener("click", (e) => { if (e.target === createModal) createModal.classList.add("hidden"); });

document.getElementById("delete-team").addEventListener("click", async () => {
    const team = teams.find((t) => t.id === openTeamId);
    if (!team) return;
    if (!confirm(`Delete "${team.name}"? Members become unassigned and their tasks lose the team. This cannot be undone.`)) return;
    try {
        await api("/teams/" + openTeamId, { method: "DELETE" });
        detail.classList.add("hidden");
        toast("Team deleted");
        loadData();
    } catch (err) { tError.textContent = err.message; }
});
document.getElementById("c-save").addEventListener("click", async () => {
    const name = document.getElementById("c-name").value.trim();
    if (!name) { cError.textContent = "Name required"; return; }
    try {
        await api("/teams/", { method: "POST", body: JSON.stringify({ name }) });
        createModal.classList.add("hidden");
        toast("Team created");
        loadData();
    } catch (err) { cError.textContent = err.message; }
});

document.getElementById("logout").addEventListener("click", () => {
    clearToken();
    window.location.href = "index.html";
});

const PERF_COLORS = ["var(--todo)", "var(--progress)", "var(--review)", "var(--done)", "var(--cat-ui_ux)"];
async function loadPerformance() {
    const box = document.getElementById("team-performance");
    if (!box) return;
    box.innerHTML = "";

    const legend = document.createElement("div");
    legend.className = "perf-legend";
    legend.innerHTML =
        `<span><span class="lg-dot" style="background:var(--done)"></span>Done</span>` +
        `<span><span class="lg-dot" style="background:var(--danger)"></span>Overdue</span>` +
        `<span><span class="lg-dot" style="background:var(--progress)"></span>Open</span>`;
    box.appendChild(legend);

    for (const team of teams) {
        let stats = [];
        try {
            stats = await api("/stats/team/" + team.id);
        } catch { continue; }

        let done = 0, open = 0, overdue = 0;
        let hoursSum = 0, hoursCount = 0;
        for (const s of stats) {
            done += s.counts.done || 0;
            open += (s.counts.todo || 0) + (s.counts.in_progress || 0) + (s.counts.pending_review || 0);
            overdue += s.overdue || 0;
            if (s.avg_completion_hours != null) {
                hoursSum += s.avg_completion_hours;
                hoursCount += 1;
            }
        }
        const total = done + open || 1;
        const pct = (n) => (n / total) * 100;
        const rate = Math.round((done / total) * 100);
        const avgHours = hoursCount ? Math.round(hoursSum / hoursCount) : null;

        const row = document.createElement("div");
        row.className = "perf-row";

        const head = document.createElement("div");
        head.className = "perf-head";
        head.innerHTML =
            `<span class="perf-name">` +
            `<span class="perf-dot" style="background:${PERF_COLORS[team.id % PERF_COLORS.length]}"></span>` +
            `${team.name}</span>` +
            `<span class="perf-nums">${rate}% done · ${open} open` +
            (overdue ? ` · <span class="perf-late">${overdue} overdue</span>` : "") +
            (avgHours != null ? ` · ~${avgHours}h avg` : "") + `</span>`;

        const bar = document.createElement("div");
        bar.className = "perf-bar";
        bar.innerHTML =
            `<div class="seg-done" style="width:${pct(done)}%"></div>` +
            `<div class="seg-late" style="width:${pct(overdue)}%"></div>` +
            `<div class="seg-open" style="width:${pct(open - overdue)}%"></div>`;

        row.append(head, bar);
        box.appendChild(row);
    }

    if (box.children.length <= 1) {
        box.innerHTML = `<div class="perf-row"><div class="perf-head">No data yet</div></div>`;
    }
}

loadMe();
loadData();