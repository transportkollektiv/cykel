from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import BasicAuthentication


class BasicTokenAuthentication(BasicAuthentication):
    """HTTP Basic authentication against api token as password (user
    ignored)"""

    www_authenticate_realm = "api token as password"
    model = None

    def get_model(self):
        if self.model is not None:
            return self.model
        from rest_framework.authtoken.models import Token

        return Token

    def authenticate_credentials(self, userid, key, request=None):
        """Authenticate the supplied password against tokens."""
        model = self.get_model()
        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_("User inactive or deleted."))

        return (token.user, token)

    def authenticate_header(self, request):
        return 'Basic realm="%s"' % self.www_authenticate_realm
