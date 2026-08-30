document.addEventListener("DOMContentLoaded", function () {

    const sidebar = document.getElementById("sidebar");

    const menuButton = document.getElementById("menuButton");

    const closeButton = document.getElementById("sidebarCloseButton");

    if (!sidebar || !menuButton) {
        return;
    }

    let overlay = document.createElement("div");

    overlay.className = "sidebar-overlay";

    document.body.appendChild(overlay);

    menuButton.addEventListener("click", function () {

        sidebar.classList.add("show");

        overlay.classList.add("show");

    });

    overlay.addEventListener("click", closeSidebar);

    if (closeButton) {
        closeButton.addEventListener("click", closeSidebar);
    }

    document.querySelectorAll("#sidebar a").forEach(function (item) {

        item.addEventListener("click", function () {

            if (window.innerWidth < 992) {

                closeSidebar();

            }

        });

    });

    function closeSidebar() {

        sidebar.classList.remove("show");

        overlay.classList.remove("show");

    }

});
