from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.urls import resolve, Resolver404


class GlobalLoginRequiredMiddleware:
    """Require authentication for all views except explicit public endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.public_url_names = set(getattr(settings, 'GLOBAL_LOGIN_EXEMPT_URL_NAMES', []))
        self.public_path_prefixes = tuple(getattr(settings, 'GLOBAL_LOGIN_EXEMPT_PATH_PREFIXES', []))

    def __call__(self, request):
        if getattr(settings, 'DISABLE_LOGIN_REQUIRED', False):
            return self.get_response(request)

        if request.user.is_authenticated:
            return self.get_response(request)

        if self._is_public_path(request.path_info):
            return self.get_response(request)

        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

    def _is_public_path(self, path):
        if path.startswith(self.public_path_prefixes):
            return True

        try:
            match = resolve(path)
        except Resolver404:
            return False

        return match.url_name in self.public_url_names
