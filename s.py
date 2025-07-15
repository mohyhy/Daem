import requests
import json

# بيانات تسجيل الدخول
session_data={
    "session_id": 1,  
    "content": "أنا أشعر بالقلق"  
}

headers = {
        'Authorization': f'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUxMjE2Mjk0LCJpYXQiOjE3NTExMjk4OTQsImp0aSI6IjJmM2ZjZWIwZjg5ZjRjMjJhZmQ2ODU0YTFkOWFkMzNlIiwidXNlcl9pZCI6MX0.O-DI7crgnzA1FGqF6EupuDVaKMOvVw0-Mz5pHwjppRg',  # إضافة التوكن في Authorization header
        'Content-Type': 'application/json'
    }

# URL للحصول على التوكن
login_url = 'http://localhost:8000/send-message/'

# إرسال POST للحصول على التوكن

response = requests.post(login_url, headers=headers, data=json.dumps(session_data))
print(response.json())