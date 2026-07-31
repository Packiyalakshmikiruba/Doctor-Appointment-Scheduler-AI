from .models import Notification


def notification_context(request):

    if request.user.is_authenticated:

        return {

            "unread_notification_count":
            Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count(),

            "recent_notifications":
            Notification.objects.filter(
                user=request.user,
            ).order_by("-created_at")[:5],

        }

    return {}