from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class UserProfile(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),      # مريض
        ('therapist', 'Therapist') # معالج
    )
    email = models.EmailField(unique=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    bio = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)





from django.utils import timezone  # استيراد مكتبة الوقت

class Session(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_sessions')
    therapist = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='therapist_sessions')
    is_ai_controlled = models.BooleanField(default=False)  # هل الجلسة 100% مع AI؟
    topic = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)  # الحقل الجديد لتحديد إذا كانت الجلسة نشطة
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    summary_generated_by_ai = models.TextField(blank=True)  # AI يلخص الجلسة
    is_completed = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
    def __str__(self):
        return f"جلسة مع {self.user.username} - {'نشطة' if self.is_active else 'منتهية'}"

#✅ الهدف: دعم جلسات يقودها الذكاء الاصطناعي (مثلاً chatbot إرشادي).

class MoodLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    session = models.OneToOneField(Session, on_delete=models.CASCADE, null=True, blank=True, related_name='mood_log')
    mood = models.CharField(max_length=50)
    notes = models.TextField(blank=True)  # المستخدم يكتب مشاعره هنا
    sentiment_score = models.FloatField(null=True, blank=True)  # هنا يتم كتابة النتيجة عن طريق مكتبات الذكاء بعد ادخال النص لها وتحليله
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Mood: {self.mood} for session {self.session.id}"
#✅ الهدف: ربط ما يقوله المستخدم مع تحليلات الـ AI عبر sentiment_score (مثلاً -1 إلى +1).
    

class AISuggestion(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    mood_log = models.ForeignKey(MoodLog, on_delete=models.CASCADE)  # ربط التوصية بملاحظة المزاج
    suggestion_text = models.TextField()
    source_type = models.CharField(max_length=50, choices=[('mood', 'Mood'), ('chat', 'Chat'), ('manual', 'Manual')])
    generated_at = models.DateTimeField(auto_now_add=True)
    accepted_by_user = models.BooleanField(default=False)
#✅ الهدف: حفظ كل توصية يقدمها الذكاء الاصطناعي لتقييم فعاليتها لاحقًا أو تعديلها.

class ChatMessage(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserProfile,null=True, blank=True, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_ai = models.BooleanField(default=False)
    sentiment = models.CharField(max_length=50, blank=True)  # مثل "غضب، قلق، حياد"
    def __str__(self):
        sender_name = self.sender.username if self.sender else "AI"
        return f"رسالة من {sender_name} في {self.timestamp}"


#✅ الهدف: كل رسالة تمر بتحليل مشاعر أو تصنيف نفسي فورًا.


class AIModelLog(models.Model):
    input_text = models.TextField()
    output_text = models.TextField()
    model_used = models.CharField(max_length=100)  # اسم النموذج: eg: BERT, GPT
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

#✅ الهدف: حفظ أداء الذكاء الاصطناعي للتقييم ومراقبة الجودة.

# input_text	output_text	model_used	user	created_at
# "أشعر بأنني فاشل..."	"sentiment:-0.85, توصية: راجع مقال..."	arabert-v02-sentiment	أحمد	2025-06-16


class Resource(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    link = models.URLField()
    category = models.CharField(max_length=100)
    tags = models.CharField(max_length=255)  # للربط مع التوصيات
    language = models.CharField(max_length=50, default='ar')
    created_at = models.DateTimeField(auto_now_add=True)
#✅ الهدف: الذكاء الاصطناعي يمكنه اقتراح مصادر تلقائيًا بناءً على tags أو mood.

