from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=500, verbose_name="책 제목")
    price = models.CharField(max_length=50, verbose_name="가격")
    rating = models.CharField(max_length=50, verbose_name="평점")
    stock = models.CharField(max_length=50, verbose_name="재고 상태")
    url = models.URLField(unique=True, verbose_name="상세 URL")
    
    # 데이터 관리용
    crawled_at = models.DateTimeField(auto_now=True, verbose_name="수집일시")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "수집된 책 데이터"
        verbose_name_plural = "수집된 책 데이터 목록"