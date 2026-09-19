from rest_framework.viewsets import ModelViewSet

from utilisateur.middleware import set_thread_user
from utilisateur.models import Utilisateur


class GimaoModelViewSet(ModelViewSet):
    """
    Base ViewSet that extracts the user from the request payload/auth
    and stores it in thread-local storage for use by signals.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        # Determine the user
        app_user = None

        # 1. From Payload (User ID)
        if hasattr(request, "data") and isinstance(request.data, dict):
            # Try various keys
            user_id = (
                request.data.get("user")
                or request.data.get("utilisateur")
                or request.data.get("utilisateur_id")
            )

            if user_id:
                # Handle dict if object passed
                if isinstance(user_id, dict):
                    user_id = user_id.get("id")

                try:
                    if user_id:
                        app_user = Utilisateur.objects.get(pk=user_id)
                except (Utilisateur.DoesNotExist, ValueError):
                    pass

        # 2. From Auth Token
        # if not app_user and request.user and request.user.is_authenticated:
        #     # Try to match Django User to app-level Utilisateur
        #     if hasattr(request.user, 'utilisateur'):
        #          app_user = request.user.utilisateur
        #     elif hasattr(request.user, 'username'):
        #          app_user = Utilisateur.objects.filter(nomUtilisateur=request.user.username).first()

        if not app_user and hasattr(request, "api_user"):
            app_user = request.api_user

        # 3. From Auth Token (ancien système)
        if not app_user and request.user and request.user.is_authenticated:
            if hasattr(request.user, "utilisateur"):
                app_user = request.user.utilisateur
            elif hasattr(request.user, "username"):
                app_user = Utilisateur.objects.filter(nomUtilisateur=request.user.username).first()

        # Save to thread local
        set_thread_user(app_user)

    def finalize_response(self, request, response, *args, **kwargs):
        # Clean up
        set_thread_user(None)
        return super().finalize_response(request, response, *args, **kwargs)
