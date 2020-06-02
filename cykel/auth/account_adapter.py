from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError


class NoSignupAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def validate_disconnect(self, account, accounts):
        raise ValidationError("Can not disconnect")

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        rent_group = Group.objects.get(name="autoenrollment-rent")

        if sociallogin.account.provider in settings.AUTOENROLLMENT_PROVIDERS:
            user.groups.add(rent_group)

        return user
