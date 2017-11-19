"""xorgauth URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

from xorgauth.accounts import views as xorgauth_views
from xorgauth.relying_party_test import views as rptest_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^openid/', include('oidc_provider.urls', namespace='oidc_provider')),
    url(r'^accounts/login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^accounts/logout/$', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^accounts/list_consents/$', xorgauth_views.list_consents, name='list_consents'),
    url(r'^test-relying-party/$', rptest_views.RelyingParty.as_view()),
]
