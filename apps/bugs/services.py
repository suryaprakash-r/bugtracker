from django.db import transaction

from .models import Bug


def generate_bug_code(project):
    """
    Generate the next sequential bug code for a project.

    Examples:
        BT-001
        BT-002
        LMS-001
    """

    prefix = project.project_key.upper()

    existing_codes = (
        Bug.objects
        .filter(
            project=project,
            bug_code__startswith=f"{prefix}-",
        )
        .values_list(
            "bug_code",
            flat=True,
        )
    )

    highest_number = 0

    for code in existing_codes:

        try:

            number = int(
                code.rsplit("-", 1)[1]
            )

            highest_number = max(
                highest_number,
                number,
            )

        except (ValueError, IndexError):

            continue


    return f"{prefix}-{highest_number + 1:03d}"