from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def notification_list(request):

    notifications = request.user.notifications.all()

    notifications.update(is_read=True)

    return render(
        request,
        "notifications/list.html",
        {
            "notifications": notifications,
        },
    )