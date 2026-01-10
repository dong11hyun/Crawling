import os
from celery import Celery

# Django의 settings 모듈을 Celery의 기본 설정으로 지정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# settings.py에서 'CELERY_'로 시작하는 설정을 가져옴
app.config_from_object('django.conf:settings', namespace='CELERY')

# 등록된 앱에서 tasks.py를 자동으로 찾음
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')