from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render

from .forms import PostForm, CommentForm
from .models import Post, Group, Comment, Follow

User = get_user_model()


def index(request):
    latest = Post.objects.all()
    paginator = Paginator(latest, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "index.html", {
        'page':page, 
        'paginator':paginator
    })
 

def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10) 
    page_number = request.GET.get('page') 
    page = paginator.get_page(page_number)
    return render(request, "group.html", {
        'page': page,
        'group': group, 
        'paginator': paginator
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'new_post.html', {
            'form':form
        })
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('index')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_profile = author.posts.all()
    if Follow.objects.filter(user=request.user.id, author=author).exists():
        following = True
    else:
        following = False
    paginator = Paginator(posts_profile, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {
        'profile':author, 
        'paginator': paginator, 
        'page_num': page_number, 
        'page':page,
        'following': following,
    })
 
 
def post_view(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post,  pk=post_id)
    following = False
    if Follow.objects.filter(user=request.user.id, author=profile).exists():
        following = True
    else:
        following = False
    form = CommentForm()
    comments = post.comment.all()
    author = post.author
    return render(request, 'post.html', {
        'profile': profile,
        'post': post,
        'form': form,
        'comments': comments,
        'following': following,
    })


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    if request.user != author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
        request.POST or None, 
        files=request.FILES or None, 
        instance=post
    )
    if not form.is_valid():
        return render(request, 'new_post.html', {
            'form': form, 
            'post': post
        })
    form.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm(request.POST  or None)
    if not form.is_valid():
        return redirect('post', username=post.author.username, post_id=post_id)
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('post', username=post.author, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user).order_by("-pub_date")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {
        "page": page, 
        "paginator": paginator
    })


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return redirect("profile", username=username)
    following = get_object_or_404(User, username=username)
    already_follows = Follow.objects.filter(user=request.user,
                                            author=following).exists()
    if not already_follows:
        Follow.objects.create(user=request.user, author=following)
    return redirect("profile", username=username)
    

@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=following).delete()
    return redirect("profile", username=username)


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500) 
