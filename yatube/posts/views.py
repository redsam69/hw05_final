from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    paginator = Paginator(posts, settings.PAGE_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj,
               }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, settings.PAGE_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj,
               'group': group,
               }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    else:
        following = False
    paginator = Paginator(posts, settings.PAGE_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'author': author,
               'page_obj': page_obj,
               'following': following,
               }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_id = get_object_or_404(Post, id=post_id)
    comments = post_id.comments.all()
    form = CommentForm()
    context = {'post': post_id,
               'form': form,
               'comments': comments,
               }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        add_form = form.save(commit=False)
        add_form.author = request.user
        add_form.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    return render(request, 'posts/create_post.html', {'form': form,
                  'post': post, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list_follow = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(post_list_follow, settings.PAGE_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj,
               }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    already = Follow.objects.filter(user=request.user, author=author).exists()
    if request.user.username == username:
        return redirect('posts:profile', request.user)
    if not already:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', request.user)


@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    follower = get_object_or_404(Follow, author=following, user=request.user)
    follower.delete()
    return redirect('posts:profile', request.user)
