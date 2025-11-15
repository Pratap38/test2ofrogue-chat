from django.utils import timezone
from django.contrib.auth.models import User

class ActiveUserMiddleware:
    """
    Middleware to track user online status and last seen.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Update last seen after response to avoid slowing request
        if request.user.is_authenticated:
            try:
                profile = request.user.profile  # assumes OneToOneField from User -> Profile
                profile.is_online = True
                profile.last_seen = timezone.now()
                profile.save(update_fields=['is_online', 'last_seen'])
            except Exception as e:
                # Avoid breaking requests if user has no profile
                print(f"ActiveUserMiddleware error: {e}")

        return response

