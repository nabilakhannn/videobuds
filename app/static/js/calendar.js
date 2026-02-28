/**
 * Calendar interactions for the VideoBuds Video Studio.
 * Handles post-card click -> side-panel open/close and HTMX after-swap.
 */

function openSidePanel(postId) {
    var panel = document.getElementById("side-panel");
    var overlay = document.getElementById("side-panel-overlay");
    if (!panel) return;

    // Load post detail via HTMX into the panel body
    var body = document.getElementById("side-panel-body");
    if (body) {
        body.innerHTML = '<div class="p-6 text-center text-gray-400">Loading...</div>';
        htmx.ajax("GET", "/posts/" + postId + "/detail", { target: "#side-panel-body", swap: "innerHTML" });
    }

    panel.classList.add("open");
    if (overlay) overlay.classList.add("open");
}

function closeSidePanel() {
    var panel = document.getElementById("side-panel");
    var overlay = document.getElementById("side-panel-overlay");
    if (panel) panel.classList.remove("open");
    if (overlay) overlay.classList.remove("open");
}

// Close panel on overlay click
document.addEventListener("click", function (e) {
    if (e.target && e.target.id === "side-panel-overlay") {
        closeSidePanel();
    }
});

// Close panel on Escape key
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        closeSidePanel();
    }
});

// After HTMX swaps new content into the calendar, re-bind post card clicks
document.addEventListener("htmx:afterSwap", function (e) {
    var cards = document.querySelectorAll(".post-card[data-post-id]");
    cards.forEach(function (card) {
        card.addEventListener("click", function () {
            openSidePanel(card.getAttribute("data-post-id"));
        });
    });
});
