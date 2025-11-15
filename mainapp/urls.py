from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('home/', views.home_view, name='home'),

    path('post/', views.post_create_view, name='post_create'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('comment/<int:post_id>/', views.add_comment_view, name='add_comment'),

    # chats
    path('chat/', views.chat_view, name='chat'),  # global chat
    path('private-chat/<str:room_name>/', views.private_chat, name='private_chat'),
    path('chathome/', views.chat_home, name='chathome'),
    path('upload-private-file/', views.upload_private_file, name='upload_private_file'),

    # groups
    path('group/create/', views.create_group, name='create_group'),
    path('group/<int:group_id>/', views.group_chat, name='group_chat'),  # single group messages
    path('group-chat/', views.group_chatpage, name='group_chatpage'),     # list of groups
    path('group/<int:group_id>/add-member/', views.add_group_member, name='add_group_member'),

    # profile & search
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('search/', views.search_user, name='search'),

    # logout
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
