if (!getToken()) window.location.href = "index.html";

const STATUS_LABELS = {
    todo: "To do", in_progress: "In progress",
    pending_review: "Pending review", done: "Done",
};

let allTasks = [];
let me = null;
let activeChip = null;
const selected = new Set();
const collapsed = new Set();

const toastEl = document.getElementById("toast");
function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    setTimeout(() => toastEl.classList.remove("show"), 3000);
}

// ---------- date helpers ----------
function today0() { const d = new Date(); d.setHours(0,0,0,0); return d; }
function dueDate(task) { return task.due_date ? new Date(task.due_date + "T00:00:00") : null; }
function isOverdue(task) {
    const d = dueDate(task);
    return d && task.status !== "done" && d < today0();
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

// ---------- load ----------
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

async function loadTasks() {
    allTasks = await api("/tasks/");
    render();
}

// ---------- filtering ----------
function val(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
}

function visibleTasks() {
    const term = val("search").toLowerCase();
    const category = val("filter-category").toLowerCase();
    const priority = val("filter-priority");

    return allTasks.filter((t) => {
        if (!t.title.toLowerCase().includes(term)) return false;
        if (category && !(t.category || "").toLowerCase().includes(category)) return false;
        if (priority && t.priority !== priority) return false;
        if (activeChip === "overdue" && !isOverdue(t)) return false;
        if (activeChip === "today" && bucketOf(t) !== "today") return false;
        if (activeChip === "mine" && (!me || t.assignee_id !== me.id)) return false;
        return true;
    });
}

// ---------- render ----------
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

            const title = document.createElement("span");
            title.className = "ttitle";
            title.textContent = task.title;

            const badge = document.createElement("span");
            badge.className = "badge " + task.priority;
            badge.textContent = task.priority;

            const cat = document.createElement("span");
            cat.className = "tmeta";
            cat.textContent = task.category || "—";

            const status = document.createElement("span");
            status.className = "tmeta";
            status.textContent = STATUS_LABELS[task.status] || task.status;

            const who = document.createElement("span");
            who.className = "tmeta";
            who.textContent = "User " + task.assignee_id;

            const due = document.createElement("span");
            due.className = "tmeta tdue" + (isOverdue(task) ? " late" : "");
            due.textContent = task.due_date || "—";

            row.append(check, title, badge, cat, status, who, due);
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
    renderGroups();
    renderBulkBar();
}

// ---------- bulk actions ----------
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

// ---------- wiring ----------
function on(id, event, handler) {
    const el = document.getElementById(id);
    if (el) el.addEventListener(event, handler);
}

on("search", "input", render);
on("filter-category", "input", render);
on("filter-priority", "change", render);
on("clear-filters", "click", () => {
    ["search", "filter-category"].forEach((id) => { const e = document.getElementById(id); if (e) e.value = ""; });
    const p = document.getElementById("filter-priority"); if (p) p.value = "";
    activeChip = null;
    render();
});
on("logout", "click", () => { clearToken(); window.location.href = "index.html"; });

loadMe();
loadTasks();