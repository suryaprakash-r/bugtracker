document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById(
                "commentForm"
            );

        const commentsList =
            document.getElementById(
                "commentsList"
            );

        const commentCount =
            document.getElementById(
                "commentCount"
            );

        const commentErrors =
            document.getElementById(
                "commentErrors"
            );

        const submitButton =
            document.getElementById(
                "commentSubmit"
            );


        if (
            !form ||
            !commentsList ||
            !commentCount ||
            !submitButton
        ) {
            return;
        }


        form.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                commentErrors.textContent = "";

                submitButton.disabled = true;

                submitButton.innerHTML =
                    '<span class="spinner-border spinner-border-sm me-1"></span> Adding...';


                try {

                    const response =
                        await fetch(
                            form.action,
                            {
                                method: "POST",

                                headers: {
                                    "X-Requested-With":
                                        "XMLHttpRequest"
                                },

                                body:
                                    new FormData(form)
                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        if (data.errors) {

                            const messageErrors =
                                data.errors.message || [];

                            commentErrors.textContent =
                                messageErrors.join(" ");

                        } else {

                            commentErrors.textContent =
                                "Unable to add the comment.";

                        }

                        return;

                    }


                    if (!data.success) {

                        commentErrors.textContent =
                            "Unable to add the comment.";

                        return;

                    }


                    const emptyState =
                        document.getElementById(
                            "commentEmptyState"
                        );


                    if (emptyState) {
                        emptyState.remove();
                    }


                    commentsList.insertAdjacentHTML(
                        "beforeend",
                        data.html
                    );


                    const currentCount =
                        Number(
                            commentCount.textContent
                        );


                    commentCount.textContent =
                        currentCount + 1;


                    form.reset();


                    commentsList
                        .lastElementChild
                        ?.scrollIntoView({
                            behavior: "smooth",
                            block: "nearest"
                        });


                } catch (error) {

                    console.error(
                        "Comment submission failed:",
                        error
                    );


                    commentErrors.textContent =
                        "Something went wrong. Please try again.";

                } finally {

                    submitButton.disabled = false;

                    submitButton.innerHTML =
                        '<i class="bi bi-chat-left-text me-1"></i> Add Comment';

                }

            }
        );

    }
);