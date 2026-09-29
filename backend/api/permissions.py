from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Изменять рецепт может только его автор."""

    def has_object_permission(self, request, view, recipe):
        return request.method in SAFE_METHODS or recipe.author == request.user
