from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import View

#to activate the user accounts
from django.http import HttpResponseRedirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.urls import reverse, NoReverseMatch
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError

#getting token from utils.py
from .utils import TokenGenerator, generate_token

#resetpassword generator
from django.contrib.auth.tokens import PasswordResetTokenGenerator

#for emails
from django.core.mail import send_mail, EmailMultiAlternatives, BadHeaderError, EmailMessage
from django.core import mail 
from django.conf import settings
#threading
import threading

class EmailThread(threading.Thread):
    def __init__(self, email_message):
        self.email_message = email_message
        threading.Thread.__init__(self)

    def run(self):
        self.email_message.send()

# Create your views here.
def userlogin(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user_obj = authenticate(username = email, password = password)

        if user_obj is not None:
            login(request, user_obj)
            messages.success(request, "Login Success!!")
            return render(request, "index.html")
        
        else:
            messages.warning(request, "Invalid Credentials!!")
            return HttpResponseRedirect(request.path_info)
    return render(request,'authentication/login.html')

def register(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password != confirm_password:
            messages.warning(request, "Password is not matching!!")
            return HttpResponseRedirect(request.path_info)
        
        try:
            if User.objects.get(username = email):
                messages.warning(request, "Email is Taken!!")
                return HttpResponseRedirect(request.path_info)
        except Exception as e:
            pass
        
        user_obj = User.objects.create_user(first_name = first_name, last_name = last_name, email = email, username = email)
        user_obj.set_password(password)
        user_obj.is_active = False
        user_obj.save()
        current_site = get_current_site(request)
        email_subject = "Activate Your Account"
        message = render_to_string('authentication/activate.html', {
            'user': user_obj,
            'domain':'127.0.0.1:8000',
            'uid': urlsafe_base64_encode(force_bytes(user_obj.pk)),
            'token': generate_token.make_token(user_obj)
        })
        
        email_message = EmailMessage(email_subject, message, settings.EMAIL_HOST_USER, [email],)
        EmailThread(email_message).start()

        messages.info(request, "Registration Successfull!! Please Verify Your Email!!")
        return redirect('/authentication/login')
    return render(request,'authentication/register.html')

def userlogout(request):
    logout(request)
    messages.success(request, "Logout Success!!")
    return redirect('/')

class ActivateAccount(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception as e:
            user =  None
            print(e)
        
        if user is not None and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.info(request, "Account Verified Successfully!!!!")
            return redirect('/authentication/login')
        
        return render(request, 'authentication/activatefailed.html')

class RequestResetEmail(View):
    def get(self, request):
        return render(request, 'authentication/request_reset_email.html')

    def post(self, request):
        email = request.POST['email']
        user = User.objects.filter(email = email)
        if user.exists():
            current_site = get_current_site(request)
            email_subject = "[Reset Your Password]"
            message = render_to_string('authentication/reset_user_password.html',{
                'domain': '127.0.0.1:8000',
                'uid': urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token': PasswordResetTokenGenerator().make_token(user[0])
            })

            email_message = EmailMessage(email_subject, message, settings.EMAIL_HOST_USER,[email])
            EmailThread(email_message).start()

            messages.info(request, "We Have Sent You an Email With Instructions!!")
            return render(request, 'authentication/request_reset_email.html')

class SetNewPassword(View):
    def get(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token,
        }

        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk = user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.warning(request, "Password Reset Link is Invalid!!")
                return render(request, 'authentication/request_reset_email.html')
        except DjangoUnicodeDecodeError as e:
            pass

        return render(request, 'authentication/set_new_password.html', context)

    def post(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token
        }

        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password != confirm_password:
            messages.warning(request, "Password is not Matching!!")
            return render(request, 'authentication/set_new_password.html', context)
        
        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
            user.set_password(password)
            user.save()
            messages.success(request, "Password Reset Successfully!!")
            return redirect('/authentication/login')
        except DjangoUnicodeDecodeError as e:
            messages.warning(request, "Something Went Wrong!!")
            return render(request, 'authentication/set_new_password', context)