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
from django.views.generic.base import TemplateView

from xorgauth.accounts import views as xorgauth_views
from xorgauth.authgroupex import views as authgpx_views
from xorgauth.relying_party_test import views as rptest_views
from xorgauth import forms as xorgauth_forms


if hasattr(auth_views, 'PasswordChangeDoneView'):
    # Django 2.1 replaced auth_password_change_done_view by PasswordChangeDoneView
    auth_password_change_done_view = auth_views.PasswordChangeDoneView.as_view()
else:
    auth_password_change_done_view = auth_views.password_change_done

urlpatterns = [
    url(r'^$', xorgauth_views.IndexView.as_view(), name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^openid/', include('oidc_provider.urls', namespace='oidc_provider')),
    url(r'^accounts/login/$',
        auth_views.LoginView.as_view(authentication_form=xorgauth_forms.AuthenticationForm),
        name='login'),
    url(r'^accounts/logout/$', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^accounts/list_consents/$', xorgauth_views.list_consents, name='list_consents'),
    url(r'^accounts/password/change/$', xorgauth_views.PasswordChangeView.as_view(), name='password_change'),
    url(r'^accounts/password/change/done/$', auth_password_change_done_view, name='password_change_done'),
    url(r'^accounts/password/reset/$', xorgauth_views.PasswordResetView.as_view(), name='password_reset'),
    url(r'^accounts/password/reset/done/$', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',  # noqa
        xorgauth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^accounts/password/reset/complete/$', auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
    url(r'^accounts/profile/$', xorgauth_views.ProfileView.as_view(), name='profile'),
    url(r'^auth-groupex$', authgpx_views.AuthGroupeXView.as_view(), name='auth-groupex'),
    url(r'^auth-groupex-login$', authgpx_views.AuthGroupeXLoginView.as_view(), name='auth-groupex-login'),
    url(r'^auth-groupex-logout$', authgpx_views.AuthGroupeXLogoutView.as_view(), name='auth-groupex-logout'),
    url(r'^sync/axdata$', xorgauth_views.SyncAxData.as_view(), name='sync-ax-data'),
    url(r'^faq$', TemplateView.as_view(template_name='faq.html'), name='faq'),
    url(r'^test-relying-party/$', rptest_views.RelyingParty.as_view(), name='test-relying-party'),
]
