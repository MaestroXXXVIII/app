from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Post
from taggit.models import Tag
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.db.models import Count
from django.core.mail import send_mail
from django.views.decorators.http import require_POST


class PostListView(ListView):
    """Список постов"""
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


class TagIndexView(ListView):
    
    model = Post
    template_name = 'blog/post/list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(tags__slug=self.kwargs.get('tag_slug') )



def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED, 
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # list active comments
    comments = post.comments.filter(active=True)
    form = CommentForm()
    
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                  .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
                                 .order_by('-same_tags', '-publish')[:4]
    return render(request, 'blog/post/detail.html', {'post': post,
                                                     'comments': comments,
                                                     'form': form,
                                                     'similar_posts': similar_posts})



def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read" \
                        f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n"\
                        f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'my_account@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post':post,
                                                    'form': form,
                                                    'sent':sent})


class AddComment(View):
    
    def post(self, request, pk):
        form = CommentForm(request.POST)
        post = Post.objects.get(id=pk)
        if form.is_valid():
            form = form.save(commit=False)
            form.post = post
            form.save()
        return redirect(post.get_absolute_url())
