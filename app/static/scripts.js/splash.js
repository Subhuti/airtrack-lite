document.addEventListener("DOMContentLoaded", function() {
    if (document.getElementById("splash")) {
        setTimeout(function() {
            document.getElementById("splash").classList.add("fade-out");
            setTimeout(function() {
                window.location.href = splashRedirectUrl;
            }, 1000);
        }, 10000);
    }
});
