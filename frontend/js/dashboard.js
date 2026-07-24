if (!getToken()) window.location.href = "index.html";

const COLUMNS = [
    { key: "todo",           label: "To do" },
    { key: "in_progress",    label: "In progress" },
    { key: "pending_review", label: "Pending review" },
    { key: "done",           label: "Done" },
];
let listLimit = 10;
const COLUMN_LIMIT = 4;
let lastBoardData = null;
const STATUS_LABELS = {
    todo: "To do", in_progress: "In progress",
    pending_review: "Pending review", done: "Done",
};
const CATEGORY_LABELS = {
    ui_ux: "UI/UX", frontend: "Frontend", backend: "Backend",
    mobile: "Mobile", devops: "DevOps",
};

const boardEl = document.getElementById("board");
const toastEl = document.getElementById("toast");

let currentUser = null;
let openTaskId = null;
let assignableUsers = [];
const userNames = new Map();

function toast(message) {
    toastEl.textContent = message;
    toastEl.classList.add("show");
    setTimeout(() => toastEl.classList.remove("show"), 3000);
}

async function loadMe() {
    const me = await api("/auth/me");
    currentUser = me;
    document.getElementById("me-name").textContent = me.name;
    document.getElementById("me-role").textContent = me.role;
    document.getElementById("avatar").textContent = me.name.slice(0, 2).toUpperCase();
    document.querySelectorAll("[data-roles]").forEach((link) => {
        const allowed = link.dataset.roles.split(",");
        if (!allowed.includes(me.role)) link.remove();
    });
}

async function loadAssignable() {
    assignableUsers = await api("/users/assignable");
    assignableUsers.forEach((u) => userNames.set(u.id, u.name));

    const select = document.getElementById("t-assignee");
    if (!select) return;
    select.innerHTML = "";
    for (const user of assignableUsers) {
        const option = document.createElement("option");
        option.value = user.id;
        option.textContent = user.name + (currentUser && user.id === currentUser.id ? " (me)" : "");
        select.appendChild(option);
    }
}
const columnModal = document.getElementById("column-backdrop");

function openColumnModal(label, tasks) {
    document.getElementById("column-title").textContent = label + " · " + tasks.length;
    const list = document.getElementById("column-list");
    list.innerHTML = "";

    for (const task of tasks) {
        const row = document.createElement("div");
        row.className = "task-row";

        const title = document.createElement("span");
        title.className = "t-title";
        title.textContent = task.title;

        const badge = document.createElement("span");
        badge.className = "badge " + task.priority;
        badge.textContent = task.priority;

        const cat = document.createElement("span");
        cat.className = "cat";
        cat.dataset.category = task.category;
        cat.textContent = CATEGORY_LABELS[task.category] || task.category;

        const who = document.createElement("span");
        who.className = "t-status";
        who.textContent = userNames.get(task.assignee_id) || ("User " + task.assignee_id);

        row.append(title, badge, cat, who);
        row.addEventListener("click", () => {
            columnModal.classList.add("hidden");
            openTask(task.id);
        });
        list.appendChild(row);
    }

    columnModal.classList.remove("hidden");
}

document.getElementById("column-close").addEventListener("click", () => {
    columnModal.classList.add("hidden");
});
columnModal.addEventListener("click", (e) => {
    if (e.target === columnModal) columnModal.classList.add("hidden");
});
function renderCard(task) {
    const card = document.createElement("div");
    card.className = "card";
    card.draggable = true;
    card.dataset.taskId = task.id;
    card.dataset.status = task.status;
    card.dataset.category = task.category;

    const title = document.createElement("div");
    title.className = "title";
    title.textContent = task.title;

    const meta = document.createElement("div");
    meta.className = "meta";

    const badge = document.createElement("span");
    badge.className = "badge " + task.priority;
    badge.textContent = task.priority;
    meta.appendChild(badge);

    const cat = document.createElement("span");
    cat.className = "cat";
    cat.dataset.category = task.category;
    cat.textContent = CATEGORY_LABELS[task.category] || task.category;
    meta.appendChild(cat);

    const who = document.createElement("span");
    who.textContent = userNames.get(task.assignee_id) || ("User " + task.assignee_id);
    meta.appendChild(who);

    if (task.due_date) {
        const due = document.createElement("span");
        due.textContent = "⏱ " + task.due_date;
        meta.appendChild(due);
    }

    card.appendChild(title);
    card.appendChild(meta);

    card.addEventListener("dragstart", () => card.classList.add("dragging"));
    card.addEventListener("dragend",   () => card.classList.remove("dragging"));
    card.addEventListener("click", () => openTask(task.id));
    return card;
}

async function loadBoard() {
    const data = await api("/tasks/board");
    boardEl.innerHTML = "";

    for (const column of COLUMNS) {
        const col = document.createElement("div");
        col.className = "column";
        col.dataset.status = column.key;

        const heading = document.createElement("h3");
        heading.textContent = column.label;
        col.appendChild(heading);

        const columnTasks = data[column.key] || [];
        for (const task of columnTasks.slice(0, COLUMN_LIMIT)) {
            col.appendChild(renderCard(task));
        }
        if (columnTasks.length > COLUMN_LIMIT) {
            const more = document.createElement("button");
            more.className = "show-more";
            more.textContent = "Show " + " more";
            more.addEventListener("click", (event) => {
                event.stopPropagation();
                openColumnModal(column.label, columnTasks);
            });
            col.appendChild(more);
        }

        col.addEventListener("dragover", (event) => {
            event.preventDefault();
            col.classList.add("drag-over");
        });
        col.addEventListener("dragleave", () => col.classList.remove("drag-over"));
        col.addEventListener("drop", async (event) => {
            event.preventDefault();
            col.classList.remove("drag-over");
            const dragged = document.querySelector(".card.dragging");
            if (!dragged) return;
            if (dragged.dataset.status === column.key) return;
            try {
                await api("/tasks/" + dragged.dataset.taskId + "/status", {
                    method: "PATCH",
                    body: JSON.stringify({ status: column.key }),
                });
            } catch (err) {
                toast(err.message);
            }
            loadBoard();
        });

        boardEl.appendChild(col);
    }

    renderTaskList(data);
}
function renderTaskList(boardData) {
    lastBoardData = boardData;
    const listEl = document.getElementById("task-list");
    if (!listEl) return;
    listEl.innerHTML = "";

    const searchEl = document.getElementById("search");
    const priorityEl = document.getElementById("filter-priority");
    const term = searchEl ? searchEl.value.toLowerCase() : "";
    const priority = priorityEl ? priorityEl.value : "";

    const allTasks = [];
    for (const column of COLUMNS) {
        for (const task of boardData[column.key] || []) {
            allTasks.push({ ...task, statusLabel: column.label });
        }
    }

    const filtered = allTasks.filter((task) =>
        task.title.toLowerCase().includes(term) &&
        (!priority || task.priority === priority)
    );

    const shown = filtered.slice(0, listLimit);

    for (const task of shown) {
        const row = document.createElement("div");
        row.className = "task-row";

        const title = document.createElement("span");
        title.className = "t-title";
        title.textContent = task.title;

        const badge = document.createElement("span");
        badge.className = "badge " + task.priority;
        badge.textContent = task.priority;

        const cat = document.createElement("span");
        cat.className = "cat";
        cat.dataset.category = task.category;
        cat.textContent = CATEGORY_LABELS[task.category] || task.category;

        const status = document.createElement("span");
        status.className = "t-status";
        status.textContent = task.statusLabel;

        row.append(title, badge, cat, status);
        row.addEventListener("click", () => openTask(task.id));
        listEl.appendChild(row);
    }

    if (filtered.length === 0) {
        listEl.innerHTML = `<div class="task-row"><span class="t-title">No tasks match</span></div>`;
        return;
    }

    const remaining = filtered.length - shown.length;
    if (remaining > 0) {
        const more = document.createElement("button");
        more.className = "show-more";
        more.textContent = "Show " + remaining + " more";
        more.addEventListener("click", () => {
            listLimit = filtered.length;
            renderTaskList(lastBoardData);
        });
        listEl.appendChild(more);
    } else if (listLimit > 10 && filtered.length > 10) {
        const less = document.createElement("button");
        less.className = "show-more";
        less.textContent = "Show less";
        less.addEventListener("click", () => {
            listLimit = 10;
            renderTaskList(lastBoardData);
        });
        listEl.appendChild(less);
    }
}

function applyListFilter() {
    if (lastBoardData) renderTaskList(lastBoardData);
}

const modal = document.getElementById("modal-backdrop");
const taskError = document.getElementById("task-error");

function openModal() {
    document.getElementById("task-form").reset();
    taskError.textContent = "";
    modal.classList.remove("hidden");
}
function closeModal() { modal.classList.add("hidden"); }

document.getElementById("new-task").addEventListener("click", openModal);
document.getElementById("modal-cancel").addEventListener("click", closeModal);
modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });

document.getElementById("task-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    taskError.textContent = "";

    const payload = {
        title:       document.getElementById("t-title").value,
        description: document.getElementById("t-desc").value,
        priority:    document.getElementById("t-priority").value,
        category:    document.getElementById("t-category").value,
    };
    const due = document.getElementById("t-due").value;
    if (due) payload.due_date = due;
    payload.assignee_id = Number(document.getElementById("t-assignee").value);

    try {
        await api("/tasks/", { method: "POST", body: JSON.stringify(payload) });
        closeModal();
        loadBoard();
    } catch (err) {
        taskError.textContent = err.message;
    }
});

const detail = document.getElementById("detail-backdrop");
const dError = document.getElementById("d-error");

async function openTask(taskId) {
    openTaskId = taskId;
    dError.textContent = "";
    detail.classList.remove("hidden");

    const task = await api("/tasks/" + taskId);
    document.getElementById("d-title").textContent = task.title;
    document.getElementById("d-desc").textContent = task.description || "";
    const pills = document.getElementById("d-pills");
    pills.innerHTML = "";

    const catPill = document.createElement("span");
    catPill.className = "pill cat-pill";
    catPill.dataset.category = task.category;
    catPill.textContent = CATEGORY_LABELS[task.category] || task.category;

    const statusPill = document.createElement("span");
    statusPill.className = "pill status-pill";
    statusPill.dataset.status = task.status;
    statusPill.textContent = STATUS_LABELS[task.status] || task.status;

    const prioPill = document.createElement("span");
    prioPill.className = "pill prio-pill";
    prioPill.dataset.priority = task.priority;
    prioPill.textContent = task.priority;

    pills.append(catPill, statusPill, prioPill);

    document.getElementById("d-sub").textContent =
        (userNames.get(task.assignee_id) || ("User " + task.assignee_id)) +
        (task.due_date ? "  ·  due " + task.due_date : "");

    const canReview = currentUser &&
        (currentUser.role === "manager" || currentUser.role === "superadmin") &&
        task.status === "pending_review";
    document.getElementById("review-box").classList.toggle("hidden", !canReview);

    loadChecklist();
    loadComments();
}

function closeDetail() {
    detail.classList.add("hidden");
    openTaskId = null;
}

document.getElementById("detail-close").addEventListener("click", closeDetail);
detail.addEventListener("click", (e) => { if (e.target === detail) closeDetail(); });

async function loadChecklist() {
    const items = await api("/tasks/" + openTaskId + "/checklist");
    const box = document.getElementById("d-checklist");
    box.innerHTML = "";

    for (const item of items) {
        const row = document.createElement("div");
        row.className = "check-item";

        const check = document.createElement("input");
        check.type = "checkbox";
        check.checked = item.done_flag;
        check.addEventListener("change", async () => {
            try {
                await api("/checklist-items/" + item.id + "/toggle", { method: "PATCH" });
                loadChecklist();
            } catch (err) { dError.textContent = err.message; }
        });

        const text = document.createElement("span");
        text.className = "text" + (item.done_flag ? " done" : "");
        text.textContent = item.text;

        const del = document.createElement("button");
        del.className = "icon-btn";
        del.textContent = "✕";
        del.addEventListener("click", async () => {
            try {
                await api("/checklist-items/" + item.id, { method: "DELETE" });
                loadChecklist();
            } catch (err) { dError.textContent = err.message; }
        });

        row.appendChild(check);
        row.appendChild(text);
        row.appendChild(del);
        box.appendChild(row);
    }
}

document.getElementById("checklist-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("d-item-text");
    if (!input.value.trim()) return;
    try {
        await api("/tasks/" + openTaskId + "/checklist", {
            method: "POST",
            body: JSON.stringify({ text: input.value }),
        });
        input.value = "";
        loadChecklist();
    } catch (err) { dError.textContent = err.message; }
});

async function loadComments() {
    const comments = await api("/tasks/" + openTaskId + "/comments");
    const box = document.getElementById("d-comments");
    box.innerHTML = "";

    for (const comment of comments) {
        const row = document.createElement("div");
        row.className = "comment-item";

        const text = document.createElement("span");
        text.className = "text";
        text.textContent = comment.text;

        const who = document.createElement("small");
        who.style.color = "var(--text-dim)";
        who.textContent = userNames.get(comment.author_id) || ("User " + comment.author_id);

        row.appendChild(text);
        row.appendChild(who);
        box.appendChild(row);
    }
}

document.getElementById("comment-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("d-comment-text");
    if (!input.value.trim()) return;
    try {
        await api("/tasks/" + openTaskId + "/comments", {
            method: "POST",
            body: JSON.stringify({ text: input.value }),
        });
        input.value = "";
        loadComments();
    } catch (err) { dError.textContent = err.message; }
});

document.querySelectorAll("#review-box .btn-small").forEach((btn) => {
    btn.addEventListener("click", async () => {
        dError.textContent = "";
        const payload = { decision: btn.dataset.decision };
        const comment = document.getElementById("d-review-comment").value;
        if (comment) payload.comment = comment;
        try {
            await api("/tasks/" + openTaskId + "/review", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            closeDetail();
            loadBoard();
        } catch (err) { dError.textContent = err.message; }
    });
});

document.getElementById("detail-delete").addEventListener("click", async () => {
    if (!confirm("Delete this task? This cannot be undone.")) return;
    try {
        await api("/tasks/" + openTaskId, { method: "DELETE" });
        closeDetail();
        loadBoard();
    } catch (err) {
        dError.textContent = err.message;
    }
});

document.getElementById("search").addEventListener("input", applyListFilter);
document.getElementById("filter-priority").addEventListener("change", applyListFilter);

document.getElementById("logout").addEventListener("click", () => {
    clearToken();
    window.location.href = "index.html";
});
async function boot() {
    await loadMe();
    try {
        await loadAssignable();
    } catch (err) {
        console.warn("assignable users unavailable:", err.message);
    }
    loadBoard();
}

boot();