document.addEventListener("DOMContentLoaded", function () {

    const searchInput =
        document.getElementById("projectSearch");

    const statusSelect =
        document.getElementById("projectStatus");

    const clearButton =
        document.getElementById("clearProjectFilters");

    const resultsContainer =
        document.getElementById("projectResults");


    if (
        !searchInput ||
        !statusSelect ||
        !resultsContainer
    ) {
        return;
    }


    let searchTimer = null;


    function buildUrl(page = 1) {

        const params = new URLSearchParams();

        const search =
            searchInput.value.trim();

        const status =
            statusSelect.value;


        if (search) {
            params.set("search", search);
        }

        if (status) {
            params.set("status", status);
        }

        if (page > 1) {
            params.set("page", page);
        }


        const queryString =
            params.toString();

        return queryString
            ? `/projects/?${queryString}`
            : "/projects/";
    }


    function updateBrowserUrl(url) {

        window.history.pushState(
            {},
            "",
            url
        );

    }


    function showLoading() {

        resultsContainer.classList.add(
            "project-results-loading"
        );

    }


    function hideLoading() {

        resultsContainer.classList.remove(
            "project-results-loading"
        );

    }


    async function loadProjects(
        page = 1,
        updateUrl = true
    ) {

        const url = buildUrl(page);


        showLoading();


        try {

            const response =
                await fetch(
                    url,
                    {
                        method: "GET",

                        headers: {
                            "X-Requested-With":
                                "XMLHttpRequest"
                        }
                    }
                );


            if (!response.ok) {
                throw new Error(
                    `Request failed: ${response.status}`
                );
            }


            const html =
                await response.text();


            resultsContainer.innerHTML = html;


            if (updateUrl) {
                updateBrowserUrl(url);
            }


            bindResultEvents();


        } catch (error) {

            console.error(
                "Project filtering failed:",
                error
            );


            resultsContainer.innerHTML = `
                <div class="dashboard-card">
                    <div class="project-empty-state">
                        <i class="bi bi-exclamation-triangle"></i>

                        <h3>
                            Unable to load projects
                        </h3>

                        <p>
                            Something went wrong while loading the results.
                            Please try again.
                        </p>

                        <button
                            type="button"
                            class="btn btn-sm btn-primary"
                            onclick="window.location.reload()"
                        >
                            Retry
                        </button>
                    </div>
                </div>
            `;

        } finally {

            hideLoading();

        }

    }


    function bindResultEvents() {

        const pageLinks =
            resultsContainer.querySelectorAll(
                ".project-page-link"
            );


        pageLinks.forEach(function (link) {

            link.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();


                    const page =
                        Number(
                            link.dataset.page
                        );


                    if (page) {

                        loadProjects(
                            page
                        );

                    }

                }
            );

        });


        const clearEmptyButton =
            document.getElementById(
                "clearProjectFiltersEmpty"
            );


        if (clearEmptyButton) {

            clearEmptyButton.addEventListener(
                "click",
                clearFilters
            );

        }

    }


    function clearFilters() {

        searchInput.value = "";

        statusSelect.value = "";


        loadProjects(
            1
        );

    }


    /* Search */

    searchInput.addEventListener(
        "input",
        function () {

            clearTimeout(
                searchTimer
            );


            searchTimer = setTimeout(
                function () {

                    loadProjects(
                        1
                    );

                },
                350
            );

        }
    );


    /* Status */

    statusSelect.addEventListener(
        "change",
        function () {

            loadProjects(
                1
            );

        }
    );


    /* Clear */

    if (clearButton) {

        clearButton.addEventListener(
            "click",
            clearFilters
        );

    }


    /* Initial pagination bindings */

    bindResultEvents();


    /* Browser Back / Forward */

    window.addEventListener(
        "popstate",
        function () {

            const params =
                new URLSearchParams(
                    window.location.search
                );


            searchInput.value =
                params.get("search") || "";


            statusSelect.value =
                params.get("status") || "";


            loadProjects(
                Number(
                    params.get("page") || 1
                ),
                false
            );

        }
    );

});