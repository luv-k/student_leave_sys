// ===========================
// Dark Mode Toggle
// ===========================
document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("darkModeToggle");
    if (!toggleBtn) return;

    toggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");

        if (document.body.classList.contains("dark-mode")) {
            localStorage.setItem("darkMode", "enabled");
        } else {
            localStorage.setItem("darkMode", "disabled");
        }
    });

    // Load previous state
    if (localStorage.getItem("darkMode") === "enabled") {
        document.body.classList.add("dark-mode");
    }
});

//============================================================================use
//<button id="darkModeToggle" class="btn btn-outline-secondary btn-sm">
//    Toggle Dark Mode
//</button>
//<script src="{{ url_for('static', filename='js/main.js') }}"></script>