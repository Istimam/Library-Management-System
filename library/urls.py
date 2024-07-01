from django.urls import path
from .views import BookDetailView, ProfileView, DepositMoneyView, RegisterView, LoginView, LogoutView, AddBookView, AddCategoryView, TransactionReportView

urlpatterns = [
    path('add_book/', AddBookView.as_view(), name='add_book'),
    path('book_detail/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
    path('add_category/', AddCategoryView.as_view(), name='add_category'),
    path('deposit/', DepositMoneyView.as_view(), name='deposit'),
    path('report/', TransactionReportView.as_view(), name='report'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]