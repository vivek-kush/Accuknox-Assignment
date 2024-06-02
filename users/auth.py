from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get(email__iexact=username)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            raise AuthenticationFailed('User not found')