from .models import Notification


def create_notification(
    *,
    recipient,
    title,
    message,
    notification_type=Notification.NotificationType.GENERAL,
    bug=None,
    project=None,
):
    """
    Create a notification for a user.

    Args:
        recipient: User who receives the notification.
        title: Short notification title.
        message: Notification message.
        notification_type: Notification.NotificationType value.
        bug: Optional related Bug.
        project: Optional related Project.

    Returns:
        Notification instance.
    """

    if not recipient:
        return None

    valid_types = {
        value for value, _ in Notification.NotificationType.choices
    }

    if notification_type not in valid_types:
        raise ValueError(
            f"Invalid notification type: {notification_type}"
        )

    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        bug=bug,
        project=project,
        is_read=False,
    )

    return notification



def notify_bug_status_change(
    *,
    bug,
    old_status,
    new_status,
    changed_by,
):
    """
    Notify relevant stakeholders when a bug status changes.

    Recipients:
        - Project Manager
        - Bug Reporter
        - Assigned Developer

    The user who performed the change is excluded.
    Duplicate recipients are removed automatically.
    """

    recipients = []

    # Project Manager
    if bug.project.manager:
        recipients.append(bug.project.manager)

    # Bug Reporter
    if bug.reporter:
        recipients.append(bug.reporter)

    # Assigned Developer
    if bug.assigned_to:
        recipients.append(bug.assigned_to)

    # Remove the user who performed the status change
    recipients = [
        user
        for user in recipients
        if user.id != changed_by.id
    ]

    # Remove duplicate users while preserving order
    unique_recipients = []
    seen_user_ids = set()

    for user in recipients:
        if user.id in seen_user_ids:
            continue

        seen_user_ids.add(user.id)
        unique_recipients.append(user)

    old_label = bug.Status(old_status).label
    new_label = bug.Status(new_status).label

    for recipient in unique_recipients:
        create_notification(
            recipient=recipient,
            title="Bug Status Updated",
            message=(
                f"Bug {bug.bug_code} status changed "
                f"from {old_label} to {new_label}."
            ),
            notification_type=(
                Notification.NotificationType.STATUS_CHANGED
            ),
            bug=bug,
            project=bug.project,
        )
        
def notify_bug_comment(
    *,
    bug,
    commenter,
):
    """
    Notify relevant stakeholders when a new comment is added.

    Recipients:
        - Project Manager
        - Bug Reporter
        - Assigned Developer

    The commenter is excluded.
    Duplicate recipients are removed.
    """

    recipients = []

    # Project Manager
    if bug.project.manager:
        recipients.append(bug.project.manager)

    # Bug Reporter
    if bug.reporter:
        recipients.append(bug.reporter)

    # Assigned Developer
    if bug.assigned_to:
        recipients.append(bug.assigned_to)

    # Do not notify the person who added the comment.
    recipients = [
        user
        for user in recipients
        if user.id != commenter.id
    ]

    # Remove duplicate users.
    unique_recipients = []
    seen_user_ids = set()

    for user in recipients:
        if user.id in seen_user_ids:
            continue

        seen_user_ids.add(user.id)
        unique_recipients.append(user)

    for recipient in unique_recipients:
        create_notification(
            recipient=recipient,
            title="New Bug Comment",
            message=(
                f"{commenter.username} added a comment to "
                f"bug {bug.bug_code} in project "
                f"{bug.project.name}."
            ),
            notification_type=(
                Notification.NotificationType.COMMENT_ADDED
            ),
            bug=bug,
            project=bug.project,
        )