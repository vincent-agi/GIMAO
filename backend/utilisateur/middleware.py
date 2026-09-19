import hashlib
import threading
import uuid

_thread_locals = threading.local()


def get_current_request():
    return getattr(_thread_locals, "request", None)


def get_current_user():
    try:
        request = get_current_request()
    except Exception:
        request = None

    if request:
        headers = getattr(request, "headers", {}) or {}
        auth = headers.get("Authorization") if hasattr(headers, "get") else None
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            try:
                from security.models import ApiToken

                api_token = ApiToken.objects.get(token_hash=token_hash)
                if api_token.is_valid():
                    return api_token.user
            except Exception:
                pass

        # Fallback pour le panel admin par exemple
        if hasattr(request, "user") and request.user.is_authenticated:
            if hasattr(request.user, "utilisateur"):
                return request.user.utilisateur
            elif hasattr(request.user, "username"):
                from .models import Utilisateur

                mapped_user = Utilisateur.objects.filter(
                    nomUtilisateur=request.user.username
                ).first()
                return mapped_user or request.user
            return request.user

    return getattr(_thread_locals, "app_user", None)


def set_thread_user(user):
    _thread_locals.app_user = user


def get_thread_user():
    return get_current_user()


def get_thread_log_group():
    return getattr(_thread_locals, "log_group_id", None)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We process request but we might rely on ViewSet to set the user
        # However, for non-ViewSet requests (admin?), we might still want to capture request
        _thread_locals.request = request
        _thread_locals.log_group_id = uuid.uuid4()

        response = self.get_response(request)
        if hasattr(_thread_locals, "request"):
            del _thread_locals.request
        if hasattr(_thread_locals, "app_user"):
            del _thread_locals.app_user
        if hasattr(_thread_locals, "log_group_id"):
            del _thread_locals.log_group_id
        return response
