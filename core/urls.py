from django.urls import path
from .views import (
    UserProfileList,
    SessionView,
    ChatMessageView,
    MoodLogListCreateView,
    AISuggestionListView,
    ResourceListCreateView,
    ResourceDetailView,
    SessionDetailView,
    PlatformStatsView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Daem Platform API",
      default_version='v1',
      description="توثيق كل الواجهات (Endpoints) الخاصة بالمنصة بشكل احترافي",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="support@daem.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    # ✅ تسجيل وعرض المستخدمين
    path('users/', UserProfileList.as_view(), name='user-list-create'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # الحصول على التوكن (Access + Refresh)

    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # تحديث Access Token باستخدام Refresh Token


    # ✅ جلسات
    path('sessions/', SessionView.as_view(), name='session'),
    path('sessions/<int:pk>/', SessionDetailView.as_view(), name='session-detail'),


    # ✅ رسائل الشات
    path('send-message/', ChatMessageView.as_view(), name='chat-messages'),

    # ✅ سجلات المزاج
    path('mood-logs/', MoodLogListCreateView.as_view(), name='mood-logs'),

    # ✅ التوصيات
    path('suggestions/', AISuggestionListView.as_view(), name='suggestions'),

    # ✅ الموارد
    path('resources/', ResourceListCreateView.as_view(), name='resource-list-create'),
    path('resources/<int:pk>/', ResourceDetailView.as_view(), name='resource-detail'),
    path('admin/status/', PlatformStatsView.as_view(), name='platform-stats'),

]
urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
