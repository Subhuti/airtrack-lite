document.addEventListener("DOMContentLoaded", function () {
    function setupLiveFilter(inputId, tableBodyId, searchType) {
        const input = document.getElementById(inputId);
        const tableBody = document.getElementById(tableBodyId);

        if (!input || !tableBody) return;

        input.addEventListener("input", function () {
            const searchText = input.value.trim();

            fetch(`/search_unified?type=${searchType}&search=${encodeURIComponent(searchText)}&page=1`)
                .then(response => response.text())
                .then(html => {
                    tableBody.innerHTML = html;
                })
                .catch(error => console.error("Search error:", error));
        });
    }

    // Works if you're still using these IDs in your layout
    setupLiveFilter("airlineSearch", "airlines-tbody", "airline");
    setupLiveFilter("aircraftSearch", "aircraft-tbody", "aircraft");
});
