from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .models import Post
from django.views.generic import ListView, DetailView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.db.models import Count
from django.core.mail import send_mail
from django.contrib.postgres.search import SearchVector, SearchQuery,\
                                           SearchRank


class PostListView(ListView):
    
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


class PostDetail(DetailView):
    
    slug_field = 'slug'
    queryset = Post.published.all()
    template_name = 'blog/post/detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        post = Post.objects.values_list('id', flat=True)
        post_tags_ids = Post.tags.values_list('id', flat=True)
        similar_posts = Post.published.filter(tags__in=post_tags_ids)\
                                      .exclude(id=post[:1])
        context["similar_posts"] = similar_posts.annotate(same_tags=Count('tags'))\
                                  .order_by('-same_tags', '-publish')[:4]
        context["form"] = CommentForm()
        return context
    

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


class AddSearch(View):

    def get(self, request):
        form = SearchForm()
        query = None
        results = []
        if 'query' in request.GET:
            form = SearchForm(request.GET)
            if form.is_valid():
                query = form.cleaned_data['query']
                search_vector = SearchVector('title', 'body', config='russian')
                search_query = SearchQuery(query, config='russian')
                results = Post.published.annotate(
                    search=search_vector,
                    rank=SearchRank(search_vector, search_query)
                    ).filter(search=search_query).order_by('-rank')
        return render(request, 'blog/post/search.html',
                     {'form': form,
                      'query': query,
                      'results': results})