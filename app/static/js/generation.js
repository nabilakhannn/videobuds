/**
 * Generation polling for the VideoBuds Video Studio.
 * Polls /generate/status/<campaign_id> every 3 seconds and updates a progress bar.
 */

var _pollTimer = null;

function startGenerationPolling(campaignId) {
    if (_pollTimer) clearInterval(_pollTimer);

    _pollTimer = setInterval(function () {
        fetch("/generate/status/" + campaignId)
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var bar = document.getElementById("generation-progress-bar");
                var label = document.getElementById("generation-progress-label");
                var total = data.total || 1;
                var completed = data.completed || 0;
                var pct = Math.round((completed / total) * 100);

                if (bar) {
                    bar.style.width = pct + "%";
                    bar.setAttribute("aria-valuenow", pct);
                }
                if (label) {
                    label.textContent = completed + " / " + total + " images generated";
                }

                // Stop polling when all posts are done (or on error status)
                if (completed >= total || data.status === "complete" || data.status === "error") {
                    stopGenerationPolling();
                    // Refresh the calendar grid via HTMX if present
                    var grid = document.getElementById("calendar-grid");
                    if (grid && typeof htmx !== "undefined") {
                        htmx.trigger(grid, "refresh");
                    }
                }
            })
            .catch(function () {
                // Network error — stop polling to avoid hammering the server
                stopGenerationPolling();
            });
    }, 3000);
}

function stopGenerationPolling() {
    if (_pollTimer) {
        clearInterval(_pollTimer);
        _pollTimer = null;
    }
}
