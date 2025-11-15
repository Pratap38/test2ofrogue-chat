import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from mainapp.routing import websocket_urlpatterns

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instabid.settings')

# Standard Django ASGI application
django_asgi_app = get_asgi_application()

# ProtocolTypeRouter defines how to handle different connection types
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # HTTP requests
    "websocket": AuthMiddlewareStack(  # WebSocket requests with user auth
        URLRouter(
            websocket_urlpatterns  # Your URL patterns for WS
        )
    ),
})
