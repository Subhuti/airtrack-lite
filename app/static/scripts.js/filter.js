document.addEventListener("DOMContentLoaded", function () {
    const filterType = document.getElementById("filter_type");
    const filterContainer = document.getElementById("filter_container");
    const applyFilterBtn = document.getElementById("applyFilter");

    if (!filterType || !filterContainer || !applyFilterBtn) {
        console.error("❌ Filter elements not found!");
        return;
    }

    function updateFilterInput() {
        if (filterType.value === "registration") {
            filterContainer.innerHTML = '<input type="text" id="registration" name="registration" class="form-control" placeholder="Enter Registration">';
        } else if (filterType.value === "airline") {
            filterContainer.innerHTML = '<select id="airlineID" name="airlineID" class="form-control"></select>';
            const newDropdown = document.getElementById("airlineID");
            if (newDropdown) {
                newDropdown.innerHTML = document.getElementById("airlineID").innerHTML;
            }
        }
    }

    applyFilterBtn.addEventListener("click", function () {
        let url = new URL(window.location.origin + "/aircraft_table");
        url.searchParams.append("filter_type", filterType.value);

        if (filterType.value === "registration") {
            const reg = document.getElementById("registration").value.trim();
            if (reg) url.searchParams.append("registration", reg);
        } else if (filterType.value === "airline") {
            const airline = document.getElementById("airlineID").value;
            if (airline) url.searchParams.append("airlineID", airline);
        }

        window.location.href = url.toString();
    });

    updateFilterInput();
    filterType.addEventListener("change", updateFilterInput);
});
