from django.urls import path
from . import views
from accounts.views import (
    CustomPasswordResetView, 
    UserListView, 
    UserUpdateView, 
    UserDeleteView, 
    LoginUserView)
from django.contrib.auth import views as auth_views



urlpatterns = [

    path('users-index', UserListView.as_view(), name="users-index"),
    path('register-user', views.register_user, name="register-user"),
    path('update-user/<int:pk>/', UserUpdateView.as_view(), name="update-user"),
    path('delete-user/', UserDeleteView.as_view(), name="delete-user"),
    path('deactivate-user/<int:pk>/', views.UserDeactivateView.as_view(), name="deactivate-user"),


    # user authentication
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', views. logout_view, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/accounts/password_reset.html'), name='password_reset_request'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='mail_list/emails/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='mail_list/emails/password_reset_complete.html'), name='password_reset_complete'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/accounts/password_change.html', success_url='/home'), name="password_change"),
    path('reset/', CustomPasswordResetView.as_view(), name='password_reset'),
]
