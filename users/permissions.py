from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsLibrarian(BasePermission):
    """Allows access only to authenticated Librarians or superusers."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'LIBRARIAN' or request.user.is_staff or request.user.is_superuser)
        )


class IsLibrarianOrReadOnly(BasePermission):
    """Authenticated Members can view (GET), but only Librarians can create/modify (POST/PUT/DELETE)."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user.role == 'LIBRARIAN' or request.user.is_staff or request.user.is_superuser
        )