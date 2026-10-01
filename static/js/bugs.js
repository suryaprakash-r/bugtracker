document.addEventListener("DOMContentLoaded", function () {

    const searchInput =
        document.getElementById("bugSearch");

    const statusSelect =
        document.getElementById("bugStatus");

    const severitySelect =
        document.getElementById("bugSeverity");

    const prioritySelect =
        document.getElementById("bugPriority");

    const clearButton =
        document.getElementById("clearBugFilters");

    const resultsContainer =
        document.getElementById("bugResults");


    if (
        !searchInput ||
        !statusSelect ||
        !severitySelect ||
        !prioritySelect ||
        !resultsContainer
    ) {
        return;
    }


    const bugListUrl =
        window.BUG_LIST_URL;


    let searchTimer = null;


    function buildUrl(page = 1) {

        const params =
            new URLSearchParams();


        const search =
            searchInput.value.trim();

        const status =
            statusSelect.value;

        const severity =
            severitySelect.value;

        const priority =
            prioritySelect.value;


        if (search) {
            params.set(
                "search",
                search
            );
        }

        if (status) {
            params.set(
                "status",
                status
            );
        }

        if (severity) {
            params.set(
                "severity",
                severity
            );
        }

        if (priority) {
            params.set(
                "priority",
                priority
            );
        }

        if (page > 1) {
            params.set(
                "page",
                page
            );
        }


        const queryString =
            params.toString();


        return queryString
            ? `${bugListUrl}?${queryString}`
            : bugListUrl;
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
            "bug-results-loading"
        );

    }


    function hideLoading() {

        resultsContainer.classList.remove(
            "bug-results-loading"
        );

    }


    async function loadBugs(
        page = 1,
        updateUrl = true
    ) {

        const url =
            buildUrl(page);


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


            resultsContainer.innerHTML =
                html;


            if (updateUrl) {

                updateBrowserUrl(
                    url
                );

            }


            bindResultEvents();


        } catch (error) {

            console.error(
                "Bug filtering failed:",
                error
            );


            resultsContainer.innerHTML = `
                <div class="dashboard-card">

                    <div class="bug-empty-state">

                        <i class="bi bi-exclamation-triangle"></i>

                        <h3>
                            Unable to load bugs
                        </h3>

                        <p>
                            Something went wrong while loading the results.
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
                ".bug-page-link"
            );


        pageLinks.forEach(
            function (link) {

                link.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();


                        const page =
                            Number(
                                link.dataset.page
                            );


                        if (page) {

                            loadBugs(
                                page
                            );

                        }

                    }
                );

            }
        );


        const clearEmptyButton =
            document.getElementById(
                "clearBugFiltersEmpty"
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

        severitySelect.value = "";

        prioritySelect.value = "";


        loadBugs(
            1
        );

    }


    /* =====================================================
       Realtime Search
       ===================================================== */

    searchInput.addEventListener(
        "input",
        function () {

            clearTimeout(
                searchTimer
            );


            searchTimer = setTimeout(
                function () {

                    loadBugs(
                        1
                    );

                },
                350
            );

        }
    );


    /* =====================================================
       Realtime Filters
       ===================================================== */

    statusSelect.addEventListener(
        "change",
        function () {

            loadBugs(
                1
            );

        }
    );


    severitySelect.addEventListener(
        "change",
        function () {

            loadBugs(
                1
            );

        }
    );


    prioritySelect.addEventListener(
        "change",
        function () {

            loadBugs(
                1
            );

        }
    );


    /* =====================================================
       Clear
       ===================================================== */

    if (clearButton) {

        clearButton.addEventListener(
            "click",
            clearFilters
        );

    }


    /* =====================================================
       Initial Pagination
       ===================================================== */

    bindResultEvents();


    /* =====================================================
       Browser Back / Forward
       ===================================================== */

    window.addEventListener(
        "popstate",
        function () {

            const params =
                new URLSearchParams(
                    window.location.search
                );


            searchInput.value =
                params.get(
                    "search"
                ) || "";


            statusSelect.value =
                params.get(
                    "status"
                ) || "";


            severitySelect.value =
                params.get(
                    "severity"
                ) || "";


            prioritySelect.value =
                params.get(
                    "priority"
                ) || "";


            loadBugs(
                Number(
                    params.get(
                        "page"
                    ) || 1
                ),
                false
            );

        }
    );

});