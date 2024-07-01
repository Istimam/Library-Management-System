from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .constants import TRANSACTION_TYPE
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=50)
    publication_date = models.DateField(default=timezone.now)
    description = models.TextField()
    image = models.ImageField(upload_to='book_images/')
    borrowing_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ManyToManyField(Category)

    def __str__(self):
        return self.title
    
class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.user.username
    
class Transaction(models.Model):
    account = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)  # Allow null and blank values
    transaction_type = models.IntegerField(choices=TRANSACTION_TYPE, null= True)
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    time = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['-time']

    
class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.IntegerField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.user.username} - {self.book.title}"