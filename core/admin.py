from django.contrib import admin
from .models import *

# إضافة النماذج إلى لوحة الإدارة
admin.site.register(Session)
admin.site.register(UserProfile)
admin.site.register(AISuggestion)
admin.site.register(MoodLog)
admin.site.register(ChatMessage)
