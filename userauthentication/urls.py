from django.urls import path
from userauthentication import views

urlpatterns = [
    path('login/', views.userlogin, name="login"),
    path('register/', views.register, name="register"),
    path('logout/', views.userlogout, name="logout"),
    path('activate/<uidb64>/<token>', views.ActivateAccount.as_view(), name="activate"),
    path('request-reset-email/', views.RequestResetEmail.as_view(), name="resetEmail"),
    path('set_new_password/<uidb64>/<token>', views.SetNewPassword.as_view(), name="set_new_password"),
]
