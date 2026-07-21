if (!getToken()) window.location.href = "index.html";

const COLUMNS = [
    { key: "todo",           label: "To do" },
    { key: "in_progress",    label: "In progress" },
    { key: "pending_review", label: "Pending review" },
    { key: "done",           label: "Done" },
];

const boardEl = document.getElementById("board");
const toastEl = document.getElementById("toast");

function toast(message) {
    toastEl.textContent = message;
    toastEl.classList.add("show");
    setTimeout(() => toastEl.classList.remove("show"), 3000);
}

async function loadMe() {
    const me = await api("/auth/me");
    document.getElementById("me-name").textContent = me.name;
    document.getElementById("me-role").textContent = me.role;
    document.getElementById("avatar").textContent =
        me.name.slice(0, 2).toUpperCase();

    document.querySelectorAll("[data-roles]").forEach(link => {
        const allowed = link.dataset.roles.split(",");
        if (!allowed.includes(me.role)) link.remove();
    });
}

function renderCard(task) {
    const card = document.createElement("div");
    card.className = "card";
    card.draggable = true;
    card.dataset.taskId = task.id;

    const title = document.createElement("div");
    title.className = "title";
    title.textContent = task.title;

    const meta = document.createElement("div");
    meta.className = "meta";

    const badge = document.createElement("span");
    badge.className = "badge " + task.priority;
    badge.textContent = task.priority;
    meta.appendChild(badge);

    if (task.due_date) {
        const due = document.createElement("span");
        due.textContent = "⏱ " + task.due_date;
        meta.appendChild(due);
    }

    card.appendChild(title);
    card.appendChild(meta);

    card.addEventListener("dragstart", () => card.classList.add("dragging"));
    card.addEventListener("dragend",  () => card.classList.remove("dragging"));
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

        for (const task of data[column.key] || []) {
            col.appendChild(renderCard(task));
        }

        col.addEventListener("dragover", event => {
            event.preventDefault();               
            col.classList.add("drag-over");
        });
        col.addEventListener("dragleave", () => col.classList.remove("drag-over"));
        col.addEventListener("drop", async event => {
            event.preventDefault();
            col.classList.remove("drag-over");
            const dragged = document.querySelector(".card.dragging");
            if (!dragged) return;
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
}

/* ---------- wiring ---------- */
document.getElementById("logout").addEventListener("click", () => {
    clearToken();
    window.location.href = "index.html";
});
document.getElementById("new-task").addEventListener("click", () =>
    toast("New task — coming in Stage 3"));

loadMe();
loadBoard();