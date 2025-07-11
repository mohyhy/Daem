from rest_framework import serializers
from .models import UserProfile, AISuggestion, MoodLog, Session, ChatMessage, AIModelLog, Resource

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        # إنشاء مستخدم جديد باستخدام create_user لضمان تشفير كلمة المرور
        user = UserProfile.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class AISuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISuggestion
        fields = '__all__'

class MoodLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodLog
        fields = '__all__'

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'
        extra_kwargs = {
            'therapist': {'required': False},  # المعالج ليس مطلوبًا في البداية
            'is_ai_controlled': {'required': False, 'default': True},  # يمكن تحديد هذه القيمة في الفيو
            'topic': {'required': True},  # الموضوع مطلوب
            'start_time': {'required': False},  # سيتم تعيينه تلقائيًا في الفيو
            'end_time': {'required': False} ,
            'user': {'required': False} # سيتم تعيينه لاحقًا أو تركه فارغًا
        }

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['session', 'sender', 'content', 'is_ai', 'sentiment']

    def create(self, validated_data):
        # يمكنك إضافة أي منطق مخصص هنا، مثل تحديد `user` تلقائيًا إذا لم يكن موجودًا.
        validated_data['sender'] = self.context['request'].user  # تعيين `sender` من `request.user`
        return super().create(validated_data)

class AIModelLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModelLog
        fields = '__all__'
    def create(self, validated_data):
        # ربط `user` تلقائيًا باستخدام `request.user` في الفيو
        user = validated_data.get('user', None)  # لا تأخذ قيمة `user` من validated_data مباشرة
        if not user:  # إذا لم يكن هناك `user` في `validated_data`
            raise serializers.ValidationError("User is required.")  # تحقق يدويًا إذا لم يتم تعيينه
        return AISuggestion.objects.create(**validated_data)


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = '__all__'
