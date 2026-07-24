if (!getToken()) window.location.href = "index.html";

const STATUS_LABELS = {
    todo: "To do", in_progress: "In progress",
    pending_review: "Pending review", done: "Done",
};

const CATEGORY_LABELS = {
    ui_ux: "UI/UX", frontend: "Frontend", backend: "Backend",
    mobile: "Mobile", devops: "DevOps",
};

const STALE_REVIEW_DAYS = 3;

let allTasks = [];
let me = null;
let activeChip = null;
const selected = new Set();
const collapsed = new Set();
const userNames = new Map();

const toastEl = document.getElementById("toast");
function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    setTimeout(() => toastEl.classList.remove("show"), 3000);
}

function nameOf(userId) {
    return userNames.get(userId) || ("User " + userId);
}

function today0() { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }
function dueDate(task) { return task.due_date ? new Date(task.due_date + "T00:00:00") : null; }
function isOverdue(task) {
    const d = dueDate(task);
    return d && task.status !== "done" && d < today0();
}
function daysSince(dateString) {
    if (!dateString) return 0;
    return Math.floor((today0() - new Date(dateString.slice(0, 10) + "T00:00:00")) / 86400000);
}
function bucketOf(task) {
    const d = dueDate(task);
    if (!d) return "none";
    if (isOverdue(task)) return "overdue";
    const diff = Math.round((d - today0()) / 86400000);
    if (diff === 0) return "today";
    if (diff <= 7) return "week";
    return "later";
}

const BUCKETS = [
    { key: "overdue", label: "Overdue", urgent: true },
    { key: "today",   label: "Due today" },
    { key: "week",    label: "This week" },
    { key: "later",   label: "Later" },
    { key: "none",    label: "No due date" },
];

async function loadMe() {
    me = await api("/auth/me");
    document.getElementById("me-name").textContent = me.name;
    document.getElementById("me-role").textContent = me.role;
    document.getElementById("avatar").textContent = me.name.slice(0, 2).toUpperCase();
    document.querySelectorAll("[data-roles]").forEach((l) => {
        if (!l.dataset.roles.split(",").includes(me.role)) l.remove();
    });
    render();
}

const teamNames = new Map();

async function loadNames() {
    const users = await api("/users/assignable");
    users.forEach((u) => userNames.set(u.id, u.name));
    if (me && me.role === "superadmin") {
        try {
            const teams = await api("/admin/teams");
            teams.forEach((t) => teamNames.set(t.id, t.name));
        } catch { /* not superadmin, ignore */ }
    }
    render();
}

async function loadTasks() {
    allTasks = await api("/tasks/");
    render();
}

function val(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
}

function visibleTasks() {
    const term = val("search").toLowerCase();
    const category = val("filter-category");
    const priority = val("filter-priority");

    return allTasks.filter((t) => {
        if (!t.title.toLowerCase().includes(term)) return false;
        if (category && t.category !== category) return false;
        if (priority && t.priority !== priority) return false;
        if (activeChip === "overdue" && !isOverdue(t)) return false;
        if (activeChip === "today" && bucketOf(t) !== "today") return false;
        if (activeChip === "mine" && (!me || t.assignee_id !== me.id)) return false;
        if (activeChip && activeChip.startsWith("user:")) {
            const id = Number(activeChip.slice(5));
            if ((t.assignee_id || 0) !== id) return false;
        }
        return true;
    });
}

function renderSummary() {
    const box = document.getElementById("summary");
    box.innerHTML = "";

    const chips = [
        { key: null,      label: "All tasks", num: allTasks.length },
        { key: "mine",    label: "Mine",      num: allTasks.filter(t => me && t.assignee_id === me.id).length },
        { key: "overdue", label: "Overdue",   num: allTasks.filter(isOverdue).length, danger: true },
        { key: "today",   label: "Due today", num: allTasks.filter(t => bucketOf(t) === "today").length },
    ];

    for (const chip of chips) {
        const el = document.createElement("div");
        el.className = "chip" + (activeChip === chip.key ? " active" : "") + (chip.danger ? " danger" : "");
        el.innerHTML = `<div class="num">${chip.num}</div><div class="lbl">${chip.label}</div>`;
        el.addEventListener("click", () => {
            activeChip = activeChip === chip.key ? null : chip.key;
            render();
        });
        box.appendChild(el);
    }
}

function renderAttention() {
    const box = document.getElementById("attention");
    if (!box) return;
    box.innerHTML = "";

    const flagged = [];
    for (const task of allTasks) {
        if (isOverdue(task)) {
            const late = -Math.round((dueDate(task) - today0()) / 86400000);
            flagged.push({ task, why: late + "d overdue", weight: 100 + late });
        } else if (task.status === "pending_review" && daysSince(task.updated_at) >= STALE_REVIEW_DAYS) {
            flagged.push({ task, why: "waiting " + daysSince(task.updated_at) + "d for review", weight: 50 });
        } else if (!task.assignee_id) {
            flagged.push({ task, why: "unassigned", weight: 10 });
        }
    }

    const panel = document.createElement("div");
    panel.className = "attention" + (flagged.length === 0 ? " clear" : "");

    if (flagged.length === 0) {
        panel.innerHTML = `<h4>Needs attention</h4>
            <div class="attention-item"><span class="name">Nothing on fire — everything is on track.</span></div>`;
        box.appendChild(panel);
        return;
    }

    flagged.sort((a, b) => b.weight - a.weight);

    const heading = document.createElement("h4");
    heading.textContent = "Needs attention · " + flagged.length;
    panel.appendChild(heading);

    for (const entry of flagged.slice(0, 5)) {
        const row = document.createElement("div");
        row.className = "attention-item";

        const badge = document.createElement("span");
        badge.className = "badge " + entry.task.priority;
        badge.textContent = entry.task.priority;

        const name = document.createElement("span");
        name.className = "name";
        name.textContent = entry.task.title;

        const why = document.createElement("span");
        why.className = "why";
        why.textContent = entry.why;

        row.append(badge, name, why);
        panel.appendChild(row);
    }

    if (flagged.length > 5) {
        const more = document.createElement("div");
        more.className = "attention-item";
        more.innerHTML = `<span class="name" style="color:var(--text-dim)">…and ${flagged.length - 5} more</span>`;
        panel.appendChild(more);
    }

    box.appendChild(panel);
}

function renderWorkload() {
    const box = document.getElementById("workload");
    if (!box) return;
    box.innerHTML = "";

    const byUser = new Map();
    for (const task of allTasks) {
        if (task.status === "done") continue;
        const id = task.assignee_id || 0;
        if (!byUser.has(id)) byUser.set(id, { open: 0, late: 0, review: 0 });
        const stats = byUser.get(id);
        stats.open++;
        if (isOverdue(task)) stats.late++;
        if (task.status === "pending_review") stats.review++;
    }

    if (byUser.size === 0) return;

    const max = Math.max(...[...byUser.values()].map((s) => s.open));
    const sorted = [...byUser.entries()].sort((a, b) => b[1].open - a[1].open);

    for (const [userId, stats] of sorted) {
        const card = document.createElement("div");
        card.className = "wl-card" + (activeChip === "user:" + userId ? " active" : "");

        const top = document.createElement("div");
        top.className = "wl-top";
        top.innerHTML =
            `<span class="wl-name">${userId === 0 ? "Unassigned" : nameOf(userId)}</span>` +
            `<span class="wl-count">${stats.open} open</span>`;

        const bar = document.createElement("div");
        bar.className = "wl-bar";
        const width = (n) => (max === 0 ? 0 : (n / max) * 100);
        bar.innerHTML =
            `<div class="seg-late" style="width:${width(stats.late)}%"></div>` +
            `<div class="seg-open" style="width:${width(stats.open - stats.late)}%"></div>`;

        const sub = document.createElement("div");
        sub.className = "wl-sub";
        const parts = [];
        if (stats.late) parts.push(stats.late + " overdue");
        if (stats.review) parts.push(stats.review + " in review");
        sub.textContent = parts.join(" · ") || "on track";

        card.append(top, bar, sub);
        card.addEventListener("click", () => {
            const key = "user:" + userId;
            activeChip = activeChip === key ? null : key;
            render();
        });

        box.appendChild(card);
    }
}

const STATUS_COLORS = {
    todo: "var(--todo)", in_progress: "var(--progress)",
    pending_review: "var(--review)", done: "var(--done)",
};

const drawer = document.getElementById("detail-backdrop");

function openDrawer(task) {
    document.getElementById("d-title").textContent = task.title;
    document.getElementById("d-accent").style.background = STATUS_COLORS[task.status] || "var(--border)";

    const pills = document.getElementById("d-pills");
    pills.innerHTML = "";
    const cat = document.createElement("span");
    cat.className = "pill cat-pill";
    cat.dataset.category = task.category;
    cat.textContent = CATEGORY_LABELS[task.category] || task.category;
    const status = document.createElement("span");
    status.className = "pill status-pill";
    status.dataset.status = task.status;
    status.textContent = STATUS_LABELS[task.status] || task.status;
    const prio = document.createElement("span");
    prio.className = "pill prio-pill";
    prio.dataset.priority = task.priority;
    prio.textContent = task.priority;
    pills.append(cat, status, prio);

    document.getElementById("d-sub").textContent = "Assigned to " + nameOf(task.assignee_id);
    document.getElementById("d-desc").textContent = task.description || "No description";

    const grid = document.getElementById("d-grid");
    grid.innerHTML = "";
    const fields = [
        ["Category", CATEGORY_LABELS[task.category] || task.category, false],
        ["Priority", task.priority, false],
        ["Status", STATUS_LABELS[task.status] || task.status, false],
        ["Assignee", nameOf(task.assignee_id), false],
        ["Due date", task.due_date || "—", isOverdue(task)],
        ["Task ID", "#" + task.id, false],
    ];
    if (me && me.role === "superadmin") {
        fields.push(["Team", teamNames.get(task.team_id) || ("Team " + task.team_id), false]);
    }
    for (const [key, value, late] of fields) {
        const field = document.createElement("div");
        field.className = "drawer-field";
        field.innerHTML = `<div class="k">${key}</div><div class="v${late ? " late" : ""}">${value}</div>`;
        grid.appendChild(field);
    }

    drawer.classList.remove("hidden");
    requestAnimationFrame(() => drawer.classList.add("show"));
}

function closeDrawer() {
    drawer.classList.remove("show");
    setTimeout(() => drawer.classList.add("hidden"), 300);
}

document.getElementById("detail-close").addEventListener("click", closeDrawer);
drawer.addEventListener("click", (e) => { if (e.target === drawer) closeDrawer(); });

function renderGroups() {
    const box = document.getElementById("groups");
    box.innerHTML = "";
    const tasks = visibleTasks();

    for (const bucket of BUCKETS) {
        const items = tasks.filter((t) => bucketOf(t) === bucket.key);
        if (items.length === 0) continue;

        const group = document.createElement("div");
        group.className = "group" + (bucket.urgent ? " urgent" : "") +
                          (collapsed.has(bucket.key) ? " collapsed" : "");

        const head = document.createElement("div");
        head.className = "group-head";
        head.innerHTML = `<span class="caret">▾</span> ${bucket.label} <span class="count">${items.length}</span>`;
        head.addEventListener("click", () => {
            collapsed.has(bucket.key) ? collapsed.delete(bucket.key) : collapsed.add(bucket.key);
            render();
        });

        const body = document.createElement("div");
        body.className = "group-body";

        for (const task of items) {
            const row = document.createElement("div");
            row.className = "trow" + (selected.has(task.id) ? " selected" : "");

            const check = document.createElement("input");
            check.type = "checkbox";
            check.checked = selected.has(task.id);
            check.addEventListener("change", () => {
                check.checked ? selected.add(task.id) : selected.delete(task.id);
                render();
            });

            const title = document.createElement("div");
            title.className = "ttitle";
            const titleLine = document.createElement("div");
            titleLine.textContent = task.title;
            const descLine = document.createElement("div");
            descLine.className = "tdesc";
            descLine.textContent = task.description || "No description";
            title.append(titleLine, descLine);

            const badge = document.createElement("span");
            badge.className = "badge " + task.priority;
            badge.textContent = task.priority;

            const cat = document.createElement("span");
            cat.className = "cat";
            cat.dataset.category = task.category;
            cat.textContent = CATEGORY_LABELS[task.category] || "—";

            const status = document.createElement("span");
            status.className = "tmeta";
            status.textContent = STATUS_LABELS[task.status] || task.status;

            const who = document.createElement("span");
            who.className = "tmeta";
            who.textContent = nameOf(task.assignee_id);

            const due = document.createElement("span");
            due.className = "tmeta tdue" + (isOverdue(task) ? " late" : "");
            due.textContent = task.due_date || "—";

            

            row.append(check, title, badge, cat, status, who, due);
            [title, badge, cat, status, who, due].forEach((el) => {
                el.style.cursor = "pointer";
                el.addEventListener("click", () => openDrawer(task));
            });
            body.appendChild(row);
        }

        group.append(head, body);
        box.appendChild(group);
    }

    if (box.children.length === 0) {
        box.innerHTML = `<div class="trow"><span class="ttitle">No tasks match these filters</span></div>`;
    }
}

function renderBulkBar() {
    const bar = document.getElementById("bulk-bar");
    bar.classList.toggle("hidden", selected.size === 0);
    document.getElementById("bulk-count").textContent = selected.size + " selected";
}

function render() {
    renderSummary();
    renderAttention();
    renderWorkload();
    renderGroups();
    renderBulkBar();
}

document.getElementById("bulk-apply").addEventListener("click", async () => {
    const status = document.getElementById("bulk-status").value;
    if (!status) return;

    let ok = 0, failed = 0;
    for (const id of [...selected]) {
        try {
            await api("/tasks/" + id + "/status", {
                method: "PATCH",
                body: JSON.stringify({ status }),
            });
            ok++;
        } catch { failed++; }
    }
    toast(`${ok} moved` + (failed ? `, ${failed} rejected` : ""));
    selected.clear();
    loadTasks();
});

document.getElementById("bulk-delete").addEventListener("click", async () => {
    if (!confirm(`Delete ${selected.size} task(s)? This cannot be undone.`)) return;
    let ok = 0, failed = 0;
    for (const id of [...selected]) {
        try { await api("/tasks/" + id, { method: "DELETE" }); ok++; }
        catch { failed++; }
    }
    toast(`${ok} deleted` + (failed ? `, ${failed} failed` : ""));
    selected.clear();
    loadTasks();
});

document.getElementById("bulk-clear").addEventListener("click", () => {
    selected.clear();
    render();
});

function on(id, event, handler) {
    const el = document.getElementById(id);
    if (el) el.addEventListener(event, handler);
}

on("search", "input", render);
on("filter-category", "change", render);
on("filter-priority", "change", render);
on("clear-filters", "click", () => {
    const s = document.getElementById("search"); if (s) s.value = "";
    const c = document.getElementById("filter-category"); if (c) c.value = "";
    const p = document.getElementById("filter-priority"); if (p) p.value = "";
    activeChip = null;
    render();
});
on("logout", "click", () => { clearToken(); window.location.href = "index.html"; });


const detail = document.getElementById("detail-backdrop");

function openDetail(task) {
    document.getElementById("d-title").textContent = task.title;

    const pills = document.getElementById("d-pills");
    pills.innerHTML = "";
    const cat = document.createElement("span");
    cat.className = "pill cat-pill";
    cat.dataset.category = task.category;
    cat.textContent = CATEGORY_LABELS[task.category] || task.category;
    const status = document.createElement("span");
    status.className = "pill status-pill";
    status.dataset.status = task.status;
    status.textContent = STATUS_LABELS[task.status] || task.status;
    const prio = document.createElement("span");
    prio.className = "pill prio-pill";
    prio.dataset.priority = task.priority;
    prio.textContent = task.priority;
    pills.append(cat, status, prio);

    document.getElementById("d-sub").textContent =
        nameOf(task.assignee_id) + (task.due_date ? "  ·  due " + task.due_date : "");
    document.getElementById("d-desc").textContent = task.description || "No description";

    detail.classList.remove("hidden");
}

document.getElementById("detail-close").addEventListener("click", () => detail.classList.add("hidden"));
detail.addEventListener("click", (e) => { if (e.target === detail) detail.classList.add("hidden"); });

loadMe();
loadNames();
loadTasks();