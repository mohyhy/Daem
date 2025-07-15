from rest_framework.permissions import BasePermission

class IsClient(BasePermission):
    """
    يتيح الوصول فقط للمستخدمين الذين دورهم Client.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'client'

class IsTherapist(BasePermission):
    """
    يتيح الوصول فقط للمعالجين.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'therapist'

class IsAdmin(BasePermission):
    """
    يتيح الوصول فقط للإدمن (is_staff).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff

class IsTherapistOrAdmin(BasePermission):
    """
    يتيح الوصول للمعالجين أو الإدمن.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.role == 'therapist' or request.user.is_staff)
        )

class IsSessionOwner(BasePermission):
    """
    يتيح الوصول فقط لصاحب الجلسة (المريض).
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class CanEditSession(BasePermission):
    """
    يتيح للمعالج تحرير الجلسة إذا كان هو المعالج المخصص، وللإدمن دائمًا.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'therapist' and obj.therapist == request.user:
            return True
        if request.user.is_staff:
            return True
        return False
