from django.urls import path

from .views import add_family_member, delete_post, edit_post, family_login, family_logout, home, news_search, post_detail, upload_photo


urlpatterns = [
    path('', home, name='home'),
    path('search/', news_search, name='news_search'),
    path('posts/<int:pk>/', post_detail, name='post_detail'),
    path('posts/<int:pk>/edit/', edit_post, name='edit_post'),
    path('posts/<int:pk>/delete/', delete_post, name='delete_post'),
    path('login/', family_login, name='family_login'),
    path('logout/', family_logout, name='family_logout'),
    path('upload-photo/', upload_photo, name='upload_photo'),
    path('add-family-member/', add_family_member, name='add_family_member'),
]