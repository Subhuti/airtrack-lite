// static/js/search.js

$(document).ready(function () {
    console.log("✅ jQuery Loaded and Ready!");

    // Airline Search
    $("#airlineSearch").on("input", function () {
        let query = $(this).val().trim();
        console.log("🔍 Searching Airlines:", query);

        $.get("/search_unified", { type: "airline", search: query })
            .done(function (partialHtml) {
                console.log("✅ AJAX Response for Airlines");
                $("#airlines-tbody").html(partialHtml);
            })
            .fail(function (error) {
                console.error("❌ AJAX Failed:", error);
            });
    });

    // Aircraft Search
    $("#aircraftSearch").on("input", function () {
        let query = $(this).val().trim();
        console.log("🔍 Searching Aircraft:", query);

        $.get("/search_unified", { type: "aircraft", search: query })
            .done(function (partialHtml) {
                console.log("✅ AJAX Response for Aircraft");

                let tbody = $("#aircraft-tbody");
                let newRows = $(partialHtml).find("tr");

                tbody.html(newRows);

                if (tbody.find('td[colspan="10"]').length > 0) {
                    $(".add-aircraft-container").fadeIn();
                } else {
                    $(".add-aircraft-container").fadeOut();
                }
            })
            .fail(function (error) {
                console.error("❌ AJAX Failed:", error);
            });
    });
});
