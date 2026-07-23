if (!getToken()) window.location.href = "index.html";

const STATUS_LABELS = {
    todo: "To do",
    in_progress: "In progress",
    pending_review: "Pending review",
    done: "Done",
};

let me = null;

async function loadMe() {
    me = await api("/auth/me");
    document.getElementById("me-name").textContent = me.name;
    document.getElementById("me-role").textContent = me.role;
    document.getElementById("avatar").textContent = me.name.slice(0, 2).toUpperCase();
    document.querySelectorAll("[data-roles]").forEach((link) => {
        if (!link.dataset.roles.split(",").includes(me.role)) link.remove();
    });
    if (me.team_id) loadTeamStats(me.team_id);
}

async function loadBoardStats() {
    const counts = await api("/stats/board");
    const box = document.getElementById("board-stats");
    box.innerHTML = "";

    for (const [status, count] of Object.entries(counts)) {
        const card = document.createElement("div");
        card.className = "stat-card";

        const num = document.createElement("div");
        num.className = "num";
        num.textContent = count;

        const lbl = document.createElement("div");
        lbl.className = "lbl";
        lbl.textContent = STATUS_LABELS[status] || status;

        card.appendChild(num);
        card.appendChild(lbl);
        box.appendChild(card);
    }
}

async function loadLeaderboard() {
    let path = "/stats/leaderboard";
    const from = document.getElementById("from-date").value;
    const to = document.getElementById("to-date").value;
    const params = [];
    if (from) params.push("from=" + from);
    if (to) params.push("to=" + to);
    if (params.length) path += "?" + params.join("&");

    const entries = await api(path);
    const box = document.getElementById("leaderboard");
    box.innerHTML = "";

    if (entries.length === 0) {
        box.innerHTML = "<div class='task-row'><span class='t-title'>No completed tasks in this range</span></div>";
        return;
    }

    entries.forEach((entry, index) => {
        const row = document.createElement("div");
        row.className = "task-row";

        const rank = document.createElement("span");
        rank.className = "rank";
        rank.textContent = "#" + (index + 1);

        const who = document.createElement("span");
        who.className = "t-title";
        who.textContent = "User " + entry.assignee_id;

        const count = document.createElement("span");
        count.className = "badge medium";
        count.textContent = entry.count + " done";

        row.appendChild(rank);
        row.appendChild(who);
        row.appendChild(count);
        box.appendChild(row);
    });
}

async function loadTeamStats(teamId) {
    const box = document.getElementById("team-stats");
    try {
        const members = await api("/stats/team/" + teamId);
        box.innerHTML = "";

        for (const member of members) {
            const row = document.createElement("div");
            row.className = "task-row";

            const who = document.createElement("span");
            who.className = "t-title";
            who.textContent = "User " + member.user_id;

            const done = document.createElement("span");
            done.className = "t-status";
            done.textContent = (member.counts.done || 0) + " done";

            const progress = document.createElement("span");
            progress.className = "t-status";
            progress.textContent = (member.counts.in_progress || 0) + " in progress";

            const overdue = document.createElement("span");
            overdue.className = "badge " + (member.overdue > 0 ? "urgent" : "low");
            overdue.textContent = member.overdue + " overdue";

            row.appendChild(who);
            row.appendChild(done);
            row.appendChild(progress);
            row.appendChild(overdue);
            box.appendChild(row);
        }
    } catch (err) {
        box.innerHTML = "<div class='task-row'><span class='t-title'>" + err.message + "</span></div>";
    }
}

document.getElementById("apply-range").addEventListener("click", loadLeaderboard);

document.getElementById("logout").addEventListener("click", () => {
    clearToken();
    window.location.href = "index.html";
});

loadMe();
loadBoardStats();
loadLeaderboard();