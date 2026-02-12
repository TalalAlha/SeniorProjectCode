from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permission class to check if user is a Super Admin."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_super_admin


class IsCompanyAdmin(permissions.BasePermission):
    """Permission class to check if user is a Company Admin."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_company_admin


class IsEmployee(permissions.BasePermission):
    """Permission class to check if user is an Employee."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_employee


class IsPublicUser(permissions.BasePermission):
    """Permission class to check if user is a Public User."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_public_user


class IsSuperAdminOrCompanyAdmin(permissions.BasePermission):
    """Permission class to check if user is either Super Admin or Company Admin."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_super_admin or request.user.is_company_admin)
        )


class HasCompanyAccess(permissions.BasePermission):
    """Permission class to check if user has access to company features."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.has_company_access


class IsSameCompany(permissions.BasePermission):
    """Permission class to check if user belongs to the same company as the object."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Super admins have access to all companies
        if request.user.is_super_admin:
            return True

        # Check if object has company attribute
        if hasattr(obj, 'company'):
            return obj.company == request.user.company

        # Check if object is the company itself
        if obj.__class__.__name__ == 'Company':
            return obj == request.user.company

        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission class to check if user is the owner of the object or an admin."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Super admins and company admins have access
        if request.user.is_super_admin or request.user.is_company_admin:
            return True

        # Check if object belongs to the user
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Check if object is the user itself
        if obj.__class__.__name__ == 'User':
            return obj == request.user

        return False
