from django.utils import timezone
from django.contrib.auth.models import User
import datetime

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = request.user.profile
            profile.is_online = True
            profile.last_seen = timezone.now()
            profile.save()

        response = self.get_response(request)
        return response
