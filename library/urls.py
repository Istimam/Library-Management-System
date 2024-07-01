from django.urls import path
from .views import BookDetailView, BorrowBookView, ProfileView, DepositMoneyView, RegisterView, LoginView, LogoutView, AddBookView, AddCategoryView

urlpatterns = [
    path('add_book/', AddBookView.as_view(), name='add_book'),
    path('add_category/', AddCategoryView.as_view(), name='add_category'),
    path('deposit/', DepositMoneyView.as_view(), name='deposit'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]