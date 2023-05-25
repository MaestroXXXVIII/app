from django.urls import path
from . import views
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('tag/<slug:tag_slug>/', views.TagIndexView.as_view(), 
         name='post_list_by_tag'),
    path("comment/<int:pk>/", views.AddComment.as_view(), name="add_comment"),
    path('<int:year>/<int:month>/<int:day>/<slug:slug>', views.PostDetail.as_view(), 
         name='post_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path("comment/<int:pk>/", views.AddComment.as_view(), name="add_comment"),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', views.AddSearch.as_view(), name='post_search'),
]
