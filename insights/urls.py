from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('upload/', views.upload_file, name='upload'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('chat/', views.chat_with_gpt, name='chat'), 
    path('portfolio/', views.portfolio, name='portfolio'), 
    path('static_view/<int:file_id>/', views.static_view, name='static_view'),
    path('download_pdf/<int:file_id>/', views.generate_pdf, name='download_pdf'),
    path('view_history/', views.view_history, name='view_history'),
    path('delete_file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),     
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),     
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),     
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]
