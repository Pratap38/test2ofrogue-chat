from django.shortcuts import render, get_object_or_404,redirect,HttpResponse
from .models import Message,Post,Comment,Profile,PrivateMessage,ChatGroup,GroupMember,GroupMessage
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage



def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        # find user by email
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user:
            login(request, user)
            return redirect('home')  # redirect after login
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'login.html')

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if email already registered
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists. Please log in.")
            return redirect("login")

        # Create a username from the email (before @ part)
        username = email.split("@")[0]

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = name
        user.save()

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")

    return render(request, "signup.html")

def chat_view(request):
    username = request.GET.get('username', 'Anonymous')
    users = User.objects.exclude(username=request.user.username)
    messages = Message.objects.all().order_by('timestamp')  # load old messages
    return render(request, 'chat.html', {
        'messages': messages,
        'username': username,
        'users': users,
    })
def home_view(request):
    posts = Post.objects.all()
    return render(request, 'home.html', {'posts': posts})
def post_create_view(request):
 

    if request.method == "POST":
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        description = request.POST.get('description')

        # save post only if user logged in
        if request.user.is_authenticated:
            Post.objects.create(
                user=request.user,
                image=image,
                video=video,
                description=description
            )
            return redirect('home')
        else:
            return redirect('login')

    return render(request, 'post.html')
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.user:
        post.delete()
        messages.success(request, "Post deleted successfully.")
    else:
        messages.error(request, "You cannot delete this post.")
    return redirect('home')
def add_comment_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Comment.objects.create(user=request.user, post=post, text=text)
    return redirect('home')


@login_required
def profile_view(request, username):
    user = request.user
    profile = getattr(user, 'profile', None)

    posts = Post.objects.filter(user=user).order_by('-timestamp') if profile else []

    if request.method == "POST" and profile:
        # Update Bio
        new_bio = request.POST.get('bio')
        if new_bio is not None:
            profile.bio = new_bio

        # Update Profile Picture
        if 'profile_pic' in request.FILES:
            profile.profile_pic = request.FILES['profile_pic']

        profile.save()
        return redirect('profile', username=username)

    context = {
        'profile': profile,
        'posts': posts,
    }
    return render(request, 'profile.html', context)

import random

def search_user(request):
    query = request.GET.get('q', '').strip()  # Get the search query
    profile = None
    posts = None

    if query:
        try:
            # Search for user by username (case-insensitive)
            user = User.objects.get(username__iexact=query)
            profile = get_object_or_404(Profile, user=user)
            # Get all posts of that user (latest first)
            posts = list(Post.objects.filter(user=user))
            # Shuffle to show random post order
            random.shuffle(posts)
        except User.DoesNotExist:
            profile = None
            posts = None
    else:
        # If no query, show random posts from all users
        posts = list(Post.objects.all())
        random.shuffle(posts)

    context = {
        'query': query,
        'profile': profile,
        'posts': posts,
    }
    return render(request, 'search.html', context)
@login_required
def private_chat(request, room_name):
    other_user = get_object_or_404(User, username=room_name)
    
    current_user = request.user

    # Ensure a consistent room name
    sorted_room = "_".join(sorted([current_user.username, other_user.username]))

    # Mark unread messages as read
    PrivateMessage.objects.filter(
        sender=other_user,
        receiver=current_user,
        is_read=False
    ).update(is_read=True)

    # Fetch old messages
    messages = PrivateMessage.objects.filter(
        sender__in=[current_user, other_user],
        receiver__in=[current_user, other_user]
    ).order_by("timestamp")

    profile = getattr(other_user, 'profile', None)

    return render(request, "private_chat.html", {
        "room_name": sorted_room,
        "receiver": other_user,
        "receiver_profile": profile,
        "messages": messages
    })




# chat home wala hia ye#
@login_required
def chat_home(request):
    users = User.objects.exclude(username=request.user.username)

    for u in users:
        u.unread = PrivateMessage.objects.filter(
            sender=u,
            receiver=request.user,
            is_read=False
        ).count()

    return render(request, "chathome.html", {
        "users": users
    })

@csrf_exempt
def upload_private_file(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        sender = request.POST.get("sender")
        receiver = request.POST.get("receiver")

        if not file or not sender or not receiver:
            return JsonResponse({"error": "Invalid data"}, status=400)

        sender_user = User.objects.get(username=sender)
        receiver_user = User.objects.get(username=receiver)

        msg = PrivateMessage.objects.create(
            sender=sender_user,
            receiver=receiver_user,
            file=file,
            content=""  # no text
        )

        file_url = request.build_absolute_uri(msg.file.url)
        return JsonResponse({"file_url": file_url})


    return JsonResponse({"error": "Only POST allowed"}, status=405)
def chat_list(request):
    users = User.objects.exclude(id=request.user.id)
    data = []

    for u in users:
        unread = Message.objects.filter(
            sender=u,
            receiver=request.user,
            is_read=False
        ).count()

        data.append({
            "user": u,
            "unread": unread
        })

    return render(request, "chat_list.html", {"data": data})
# views.py
@login_required
def group_chat(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)

    members = group.members.all()
    messages = group.messages.all()

    return render(request, "group_chat.html", {
        "group": group,
        "members": members,
        "messages": messages
    })
@login_required
def create_group(request):
    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")
        members = request.POST.getlist("members")

        group = ChatGroup.objects.create(
            name=name,
            image=image,
            created_by=request.user
        )

        # Add creator
        GroupMember.objects.create(group=group, user=request.user, is_admin=True)

        # Add selected members
        for mem in members:
            user_obj = User.objects.get(id=mem)
            GroupMember.objects.create(group=group, user=user_obj)

        return redirect("group_chat", group.id)

    users = User.objects.exclude(id=request.user.id)
    return render(request, "create_group.html", {"users": users})

@login_required
def add_group_member(request, group_id):
    group = ChatGroup.objects.get(id=group_id)

    # only creator can add members
    if group.created_by != request.user:
        return HttpResponse("Not allowed")

    if request.method == "POST":
        members = request.POST.getlist("members")
        for m in members:
            group.members.add(m)
        return redirect("group_chat", group_id=group_id)

    users = User.objects.exclude(id__in=group.members.all().values_list("id"))
    return render(request, "add_member.html", {"group": group, "users": users})

@login_required
def group_chat(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)

    # Check if current user is a member
    if not GroupMember.objects.filter(group=group, user=request.user).exists():
        return redirect("home")  # or show permission denied

    # Fetch old messages
    messages = GroupMessage.objects.filter(group=group).order_by("timestamp")

    return render(request, "group_chat.html", {
        "group": group,
        "messages": messages,
    })
@login_required
def group_chatpage(request):
    return render(request,"group_chat.html")
@login_required
def group_list(request):
    # Get all groups where the user is a member
    group_ids = GroupMember.objects.filter(user=request.user).values_list('group_id', flat=True)
    groups = ChatGroup.objects.filter(id__in=group_ids)
    return render(request, "group_list.html", {"groups": groups})
@login_required
def group_chat_view(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    
    # Check if the user is a member
    if not GroupMember.objects.filter(group=group, user=request.user).exists():
        return redirect("group_list")

    messages = group.messages.all().order_by("timestamp")
    members = group.members.all()
    return render(request, "group_chat.html", {
        "group": group,
        "messages": messages,
        "members": members
    })
