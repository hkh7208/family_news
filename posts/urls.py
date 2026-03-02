from django.urls import path

from .views import add_comment, add_family_member, approve_member, check_username, delete_member, delete_post, edit_member, edit_post, family_login, family_logout, family_signup, home, member_management, news_search, pending_approvals, post_detail, upload_photo


urlpatterns = [
    path('', home, name='home'),
    path('search/', news_search, name='news_search'),
    path('posts/<int:pk>/', post_detail, name='post_detail'),
    path('posts/<int:pk>/comments/add/', add_comment, name='add_comment'),
    path('posts/<int:pk>/edit/', edit_post, name='edit_post'),
    path('posts/<int:pk>/delete/', delete_post, name='delete_post'),
    path('login/', family_login, name='family_login'),
    path('signup/', family_signup, name='family_signup'),
    path('signup/check-username/', check_username, name='check_username'),
    path('logout/', family_logout, name='family_logout'),
    path('upload-photo/', upload_photo, name='upload_photo'),
    path('add-family-member/', add_family_member, name='add_family_member'),
    path('members/', member_management, name='member_management'),
    path('members/<int:user_id>/edit/', edit_member, name='edit_member'),
    path('members/<int:user_id>/delete/', delete_member, name='delete_member'),
    path('approvals/', pending_approvals, name='pending_approvals'),
    path('approvals/<int:user_id>/approve/', approve_member, name='approve_member'),
]