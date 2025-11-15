# from django.urls import re_path
# from . import consumers

# websocket_urlpatterns = [
#     re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
    
# ]
from django.urls import re_path
from . import consumers
from .consumers import GroupChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/", consumers.ChatConsumer.as_asgi()),
    # re_path(r"ws/private/(?P<room_name>[\w\-]+)/", consumers.PrivateChatConsumer.as_asgi()),
     # re_path(r"^ws/private/(?P<room_name>[\w\-]+)/$", consumers.PrivateChatConsumer.as_asgi()),
re_path(r"ws/private/(?P<room_name>[\w\-]+)/$", consumers.PrivateChatConsumer.as_asgi()),

      re_path(r"ws/group/(?P<group_id>\w+)/$", GroupChatConsumer.as_asgi()),
]
