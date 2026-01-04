"""Native macOS notifications using UserNotifications framework."""

import uuid


def request_notification_permission() -> None:
    """Request notification permission from user.

    This should be called on first launch to request notification permissions.
    The user will see a system dialog asking to allow notifications.
    """
    from UserNotifications import (
        UNAuthorizationOptionAlert,
        UNAuthorizationOptionSound,
        UNUserNotificationCenter,
    )

    center = UNUserNotificationCenter.currentNotificationCenter()

    def completion_handler(granted: bool, error: object) -> None:
        pass

    center.requestAuthorizationWithOptions_completionHandler_(
        UNAuthorizationOptionAlert | UNAuthorizationOptionSound,
        completion_handler,
    )


def notify(title: str, message: str) -> bool:
    """Send a native macOS notification.

    Args:
        title: Notification title.
        message: Notification body text.

    Returns:
        True if notification was sent successfully.
    """
    try:
        from UserNotifications import (
            UNMutableNotificationContent,
            UNNotificationRequest,
            UNUserNotificationCenter,
        )

        center = UNUserNotificationCenter.currentNotificationCenter()

        content = UNMutableNotificationContent.alloc().init()
        content.setTitle_(title)
        content.setBody_(message)
        content.setSound_(None)

        request_id = str(uuid.uuid4())
        request = UNNotificationRequest.requestWithIdentifier_content_trigger_(
            request_id, content, None
        )

        def completion_handler(error: object) -> None:
            pass

        center.addNotificationRequest_withCompletionHandler_(
            request, completion_handler
        )
        return True
    except Exception:
        return False


def check_notification_permission() -> bool:
    """Check if notification permission is granted.

    Returns:
        True if notifications are authorized.
    """
    try:
        from UserNotifications import (
            UNAuthorizationStatusAuthorized,
            UNUserNotificationCenter,
        )

        center = UNUserNotificationCenter.currentNotificationCenter()

        result: list[bool] = [False]

        def completion_handler(settings: object) -> None:
            if settings is not None:
                status = settings.authorizationStatus()  # type: ignore[attr-defined]
                result[0] = status == UNAuthorizationStatusAuthorized

        center.getNotificationSettingsWithCompletionHandler_(
            completion_handler
        )

        return result[0]
    except Exception:
        return False


def set_notification_delegate() -> None:
    """Set up notification delegate for handling user interactions.

    This allows the app to receive notification events even when running
    as a menu bar app.
    """
    try:
        from Foundation import NSObject
        from UserNotifications import (
            UNUserNotificationCenter,
            UNUserNotificationCenterDelegate,
        )

        class NotificationDelegate(
            NSObject,  # type: ignore[misc]
            protocols=[UNUserNotificationCenterDelegate],  # type: ignore[call-arg]
        ):
            """Delegate for handling notification events."""

            def userNotificationCenter_willPresentNotification_withCompletionHandler_(  # noqa: N802, E501
                self,
                center: object,
                notification: object,
                completion_handler: object,
            ) -> None:
                """Handle notification when app is in foreground."""
                from UserNotifications import (
                    UNNotificationPresentationOptionBanner,
                )

                completion_handler(UNNotificationPresentationOptionBanner)  # type: ignore[operator]

        center = UNUserNotificationCenter.currentNotificationCenter()
        delegate = NotificationDelegate.alloc().init()
        center.setDelegate_(delegate)

        global _notification_delegate
        _notification_delegate = delegate

    except Exception:
        pass


_notification_delegate: object = None
