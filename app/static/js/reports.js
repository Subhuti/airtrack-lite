document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ reports.js loaded");

    var disclaimerModal = document.getElementById("disclaimerModal");

    if (disclaimerModal) {
        console.log("✅ Found disclaimerModal in the HTML");

        var modalInstance = new bootstrap.Modal(disclaimerModal);

        // Just show the modal on page load (static behavior)
        modalInstance.show();

        document.getElementById("acceptDisclaimer").addEventListener("click", function () {
            modalInstance.hide();  // Just hide it, no server communication
        });

    } else {
        console.log("❌ Modal not found in the HTML");
    }
});
