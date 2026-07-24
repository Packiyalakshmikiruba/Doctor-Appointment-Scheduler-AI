from django import template
from notifications.models import Notification

register = template.Library()


@register.simple_tag
def unread_notifications_count(user):
    if not user.is_authenticated:
        return 0

    return Notification.objects.filter(
        user=user,
        is_read=False
    ).count()


@register.simple_tag
def recent_notifications(user, limit=5):
    if not user.is_authenticated:
        return []

    return Notification.objects.filter(
        user=user
    ).order_by("-created_at")[:limit]