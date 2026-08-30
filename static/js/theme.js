document.addEventListener("DOMContentLoaded", function () {

    const html = document.documentElement;
    const themeButton = document.getElementById("themeButton");

    const savedTheme = localStorage.getItem("aps_theme");

    if (savedTheme) {

        html.setAttribute("data-bs-theme", savedTheme);

        updateThemeIcon(savedTheme);

    }

    if (themeButton) {

        themeButton.addEventListener("click", function () {

            let currentTheme = html.getAttribute("data-bs-theme");

            let newTheme = currentTheme === "dark" ? "light" : "dark";

            html.setAttribute("data-bs-theme", newTheme);

            localStorage.setItem("aps_theme", newTheme);

            updateThemeIcon(newTheme);

        });

    }

    function updateThemeIcon(theme) {

        if (!themeButton) {
            return;
        }

        if (theme === "dark") {

            themeButton.innerHTML = '<i class="bi bi-sun-fill"></i>';

        } else {

            themeButton.innerHTML = '<i class="bi bi-moon-fill"></i>';

        }

    }

});