from django.contrib import admin
from .models import Book, Category, UserAccount, Transaction, Review
# Register your models here.
admin.site.register(Book)
admin.site.register(Category)
admin.site.register(UserAccount)
admin.site.register(Transaction)
admin.site.register(Review)