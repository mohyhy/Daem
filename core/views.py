from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.utils import timezone
from django.db.utils import IntegrityError
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import *
from .serializers import (
    UserRegistrationSerializer, SessionSerializer, ChatMessageSerializer,
    AISuggestionSerializer, MoodLogSerializer, ResourceSerializer
)
from .utils.sentiment_utils import analyze_sentiment_scoring, generate_support_reply
from .utils.session_utils import refresh_session_activity
from .permissions import IsClient, IsAdmin, IsTherapist, IsTherapistOrAdmin, IsSessionOwner, CanEditSession

# ✅ تسجيل وعرض المستخدمين
class UserProfileList(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request):
        users = UserProfile.objects.all()
        serializer = UserRegistrationSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "تم تسجيل المستخدم بنجاح!",
                "user": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        # ترجع الأخطاء المفصلة من الفاليديشن
        return Response({
            "message": "فشل التسجيل.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserRegistrationSerializer(request.user)
        return Response(serializer.data)

# ✅ جلسات المستخدم (Client فقط)
class SessionView(APIView):
    permission_classes = [IsClient|IsAdmin]

    def get(self, request):
        active_session = Session.objects.filter(user=request.user, is_active=True).first()
        now = timezone.now()

        if active_session:
            if now - active_session.last_activity > timedelta(minutes=30):
                active_session.is_active = False
                active_session.end_time = now
                active_session.save()
                return Response({"message": "تم إنهاء الجلسة بسبب الجمود."}, status=status.HTTP_200_OK)

            refresh_session_activity(active_session)

            data = {
                'session_id': active_session.id,
                'start_time': active_session.start_time,
                'is_ai_controlled': active_session.is_ai_controlled
            }
            return Response(data, status=status.HTTP_200_OK)

        return Response({"message": "لا توجد جلسة نشطة حالياً."}, status=status.HTTP_404_NOT_FOUND)
    def post(self, request):
        now = timezone.now()
        active_session = Session.objects.filter(user=request.user, is_active=True).first()

        if active_session:
            if now - active_session.last_activity > timedelta(minutes=30):
                active_session.is_active = False
                active_session.end_time = now
                active_session.save()
                new_session = Session.objects.create(
                    user=request.user,
                    start_time=now,
                    is_active=True,
                    is_ai_controlled=True
                )
                return Response({
                    'message': 'تم إنشاء جلسة جديدة بعد انتهاء القديمة بسبب الجمود.',
                    'session_id': new_session.id
                }, status=status.HTTP_201_CREATED)

            else:
                refresh_session_activity(active_session)
                return Response({
                    'message': 'الجلسة الحالية ما زالت نشطة.',
                    'session_id': active_session.id
                }, status=status.HTTP_200_OK)

        new_session = Session.objects.create(
            user=request.user,
            start_time=now,
            is_active=True,
            is_ai_controlled=True
        )
        return Response({
            'message': 'تم إنشاء جلسة جديدة.',
            'session_id': new_session.id
        }, status=status.HTTP_201_CREATED)
class SessionDetailView(APIView):
    permission_classes = [IsSessionOwner | CanEditSession | IsAdmin]

    def get(self, request, pk):
        session = get_object_or_404(Session, pk=pk)
        serializer = SessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        session = get_object_or_404(Session, pk=pk)
        serializer = SessionSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'تم تحديث الجلسة بنجاح.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'message': 'فشل التحديث.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        session = get_object_or_404(Session, pk=pk)
        session.is_active = False
        session.end_time = timezone.now()
        session.save()
        return Response({"message": "تم إنهاء الجلسة بنجاح."}, status=status.HTTP_200_OK)

    

# ✅ رسائل الشات (Client صاحب الجلسة أو Therapist أو Admin)
class ChatMessageView(APIView):
    permission_classes = [IsSessionOwner | CanEditSession]

    @swagger_auto_schema(
        operation_description="إرسال رسالة من المستخدم للذكاء الاصطناعي",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['session', 'content'],
            properties={
                'session': openapi.Schema(type=openapi.TYPE_INTEGER, description='معرّف الجلسة'),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='نص الرسالة')
            }
        ),
        responses={
            200: openapi.Response(
                description="رد الذكاء الاصطناعي",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'ai_response': openapi.Schema(type=openapi.TYPE_STRING),
                        'sentiment': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: "الجلسة غير موجودة"
        }
    )

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        session_id = request.data.get('session')
        content = request.data.get('content')

        if not session_id or not content:
            return Response({"message": "session_id و content مطلوبين."}, status=status.HTTP_400_BAD_REQUEST)

        session = get_object_or_404(Session, id=session_id, is_active=True)
        refresh_session_activity(session)

        detected_mood ,sentiment_score = analyze_sentiment_scoring(content)
        ai_response = generate_support_reply(detected_mood)

        user_message = ChatMessage.objects.create(
            session=session,
            sender=request.user,
            content=content,
            is_ai=False,
            sentiment=detected_mood
        )

        ai_user, created = UserProfile.objects.get_or_create(username='AI_Bot', defaults={
            'email': 'ai@daem.com',
            'role': 'therapist',
            'is_verified': True
        })

        ai_message = ChatMessage.objects.create(
            session=session,
            sender=ai_user,
            content=ai_response,
            is_ai=True,
            sentiment=detected_mood
        )

        if hasattr(session, 'mood_log'):
    # ✅ موجود → نحدثه
            mood_log = session.mood_log
            mood_log.mood = detected_mood
            mood_log.notes = f"تحديث المزاج أثناء الجلسة بناءً على الرسالة: {content[:30]}..."
            mood_log.save()
        else:
            # ✅ ما في → ننشئ جديد
            mood_log = MoodLog.objects.create(
                user=request.user,
                session=session,
                mood=detected_mood,
                notes=f"إنشاء المزاج الأول للجلسة بناءً على الرسالة: {content[:30]}...",
                sentiment_score=sentiment_score
            )


        suggestion = AISuggestion.objects.create(
            user=request.user,
            mood_log=mood_log,
            suggestion_text=ai_response,
            source_type="chat"
        )

        return Response({
            'message': 'تم إرسال الرسالة بنجاح',
            'user_message': user_message.content,
            'ai_response': ai_response,
            'suggestion': suggestion.suggestion_text,
            'detected_mood': detected_mood
        }, status=status.HTTP_201_CREATED)

# ✅ سجلات المزاج (Client فقط)
class MoodLogListCreateView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        logs = MoodLog.objects.filter(user=request.user)
        serializer = MoodLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MoodLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "message": "تم إنشاء السجل بنجاح.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ التوصيات (Client فقط)
class AISuggestionListView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        suggestions = AISuggestion.objects.filter(user=request.user)
        serializer = AISuggestionSerializer(suggestions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ✅ الموارد (الكل يستطيع القراءة، الإنشاء والتعديل Admin فقط)
class ResourceListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [AllowAny()]

    def get(self, request):
        resources = Resource.objects.all()
        serializer = ResourceSerializer(resources, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ResourceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "تم إنشاء المورد بنجاح.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResourceDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        serializer = ResourceSerializer(resource)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        serializer = ResourceSerializer(resource, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "تم تحديث المورد بنجاح.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        resource.delete()
        return Response({"message": "تم حذف المورد بنجاح."}, status=status.HTTP_204_NO_CONTENT)
class PlatformStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # عدد المستخدمين
        total_users = UserProfile.objects.count()
        total_clients = UserProfile.objects.filter(role='client').count()
        total_therapists = UserProfile.objects.filter(role='therapist').count()

        # عدد الجلسات
        total_sessions = Session.objects.count()
        active_sessions = Session.objects.filter(is_active=True).count()
        completed_sessions = Session.objects.filter(is_completed=True).count()

        # عدد الرسائل
        total_messages = ChatMessage.objects.count()

        # عدد سجلات المزاج
        total_mood_logs = MoodLog.objects.count()

        # عدد التوصيات
        total_suggestions = AISuggestion.objects.count()

        # عدد الموارد
        total_resources = Resource.objects.count()

        # تاريخ اليوم
        today = timezone.now().date()

        # جلسات اليوم
        today_sessions = Session.objects.filter(start_time__date=today).count()

        # إعداد الرد
        data = {
            "users": {
                "total": total_users,
                "clients": total_clients,
                "therapists": total_therapists,
            },
            "sessions": {
                "total": total_sessions,
                "active": active_sessions,
                "completed": completed_sessions,
                "today": today_sessions,
            },
            "messages": total_messages,
            "mood_logs": total_mood_logs,
            "suggestions": total_suggestions,
            "resources": total_resources,
        }

        return Response({
            "message": "تم جلب إحصائيات المنصة بنجاح.",
            "data": data
        }, status=status.HTTP_200_OK)