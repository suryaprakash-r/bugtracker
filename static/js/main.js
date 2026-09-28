document.addEventListener("DOMContentLoaded", function () {

    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarClose = document.getElementById("sidebarClose");
    const sidebarOverlay = document.getElementById("sidebarOverlay");


    function openSidebar() {

        if (!sidebar) {
            return;
        }

        sidebar.classList.add("sidebar-open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.add("active");
        }

    }


    function closeSidebar() {

        if (!sidebar) {
            return;
        }

        sidebar.classList.remove("sidebar-open");

        if (sidebarOverlay) {
            sidebarOverlay.classList.remove("active");
        }

    }


    /* Open sidebar */

    if (sidebarToggle) {

        sidebarToggle.addEventListener(
            "click",
            openSidebar
        );

    }


    /* Close sidebar */

    if (sidebarClose) {

        sidebarClose.addEventListener(
            "click",
            closeSidebar
        );

    }


    /* Close by clicking overlay */

    if (sidebarOverlay) {

        sidebarOverlay.addEventListener(
            "click",
            closeSidebar
        );

    }


    /* Close sidebar when navigation link is clicked */

    if (sidebar) {

        const sidebarLinks =
            sidebar.querySelectorAll(".sidebar-link");

        sidebarLinks.forEach(function (link) {

            link.addEventListener(
                "click",
                closeSidebar
            );

        });

    }


    /* Close sidebar when returning to desktop */

    window.addEventListener(
        "resize",
        function () {

            if (window.innerWidth > 992) {
                closeSidebar();
            }

        }
    );

});