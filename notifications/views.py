from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_index(request):
    notifications = Notification.objects.filter(user=request.user)
    # Mark all as read
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/index.html', {'notifications': notifications})


@login_required
def unread_count(request):
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    return JsonResponse({'count': count})
