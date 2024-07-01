from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from .models import Book, Category, Review, Transaction, User, UserAccount
from .forms import ReviewForm, BookForm, CategoryForm, DepositForm
from django.views.generic import ListView, DetailView, FormView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .constants import DEPOSIT, BORROW, PAY
# Create your views here.

# def home(request):
#     books = Book.objects.all()
#     categories = Category.objects.all()
#     return render(request, 'home.html', {'books': books, 'categories': categories})

    
class AddBookView(LoginRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'add_book.html'
    success_url = reverse_lazy('home')

class AddCategoryView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'add_category.html'
    success_url = reverse_lazy('home')

# def book_detail(request, book_id):
#     book = get_object_or_404(Book, id=book_id)
#     reviews = Review.objects.filter(book=book)
#     if request.method == 'POST':
#         form = ReviewForm(request.POST)
#         if form.is_valid():
#             review = form.save(commit=False)
#             review.book = book
#             review.save()
#             return redirect('book_detail', book_id=book.id)
#         else:
#             form = ReviewForm()
#         return render(request, 'book_detail.html', {'book':book, 'reviews':reviews, 'form':form})

class BookDetailView(DetailView):
    model = Book
    template_name = 'book_detail.html'
    context_object_name = 'book'
    from_class = ReviewForm

    def get_success_url(self):
        return reverse_lazy('book_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = Review.objects.filter(book=self.object)
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            review = form.save(commit=True)
            review.book = self.object
            review.user - request.user.userprofile
            review.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
class BorrowBookView(LoginRequiredMixin, View):
    login_url = 'login'
    def post(self, request, *args, **kwargs):
        book = get_object_or_404(Book, id=kwargs['book_id'])
        user_profile = request.user.userprofile
        if user_profile.balance >= book.borrowing_price:
            user_profile.balance -= book.borrowing_price
            user_profile.save()
            book.borrowed_by = user_profile
            book.save()
            Transaction.objects.create(
                user=user_profile, 
                book=book, 
                transaction_type='borrow', 
                amount=book.borrowing_price)
            messages.success(self.request, f"{book} book borrowed seccesfully.")
            mail_subject = "Book Borrowed From Library"
            message = render_to_string('borrow_message.html',{
                'book':book,
                'user':self.request.user
            })
            to_email = self.request.user.email
            send_email = EmailMultiAlternatives(mail_subject, '', 'nasrullah9867@gmail.com', to = [to_email])
            send_email.attach_alternative(message, "text/html")
            send_email.send()
        else:
            messages.error(self.request, "Insufficient balance.")
        return redirect('profile')

class ProfileView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'profile.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        return Transaction.objects.filter(account=self.request.user.useraccount).order_by('-time')

    
# class DepositView(LoginRequiredMixin, View):
#     template_name = 'deposit.html'
#     form_class = DepositForm
#     title = 'Deposit'

#     def get_initial(self):
#         initial = {'transaction_type': DEPOSIT}  # Assuming DEPOSIT is defined somewhere
#         return initial

#     def form_valid(self, form):
#         amount = form.cleaned_data.get('amount')
#         user_profile = self.request.user.userprofile
#         user_profile.balance += amount
#         user_profile.save(update_fields=['balance'])
        
#         messages.success(self.request, f"{amount}$ Deposited Successfully")

#         # Sending email notification
#         mail_subject = "Money Deposited"
#         message = render_to_string('deposit_message.html', {
#             'user': self.request.user,
#             'amount': amount,
#         })
#         to_email = self.request.user.email
#         send_email = EmailMultiAlternatives(mail_subject, '', 'nasrullah9867@gmail.com', [to_email])
#         send_email.attach_alternative(message, "text/html")
#         send_email.send()

#         return super().form_valid(form)
class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'deposit.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.useraccount
        })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title' : self.title,
        })
        return context
def send_transaction_mail(user, amount, subject, template):
    mail_subject = "Deposite Message"
    message = render_to_string(template,{
        'user': user,
        'amount': amount,
    })
    send_mail = EmailMultiAlternatives(subject,'','nasrullah9867@gmail.com', to=[user.email])
    send_mail.attach_alternative(message, "text/html")
    send_mail.send()

class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.useraccount
        account.balance += amount
        account.save(update_fields=['balance'])
        messages.success(self.request, f"{amount}$ was deposited to your account")
        send_transaction_mail(self.request.user, amount, "Deposit Message", "deposite_message.html")

        return super().form_valid(form)
# class DepositView(LoginRequiredMixin, View):
#     template_name = 'deposit.html'
#     form_class = DepositForm
#     title = 'Deposit'

#     def get_initial(self):
#         return {'transaction_type': 'deposit'}

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['account'] = self.request.user.userprofile
#         return kwargs

#     def get(self, request, *args, **kwargs):
#         form = self.form_class(initial=self.get_initial())
#         return render(request, self.template_name, {'form': form, 'title': self.title})

#     def post(self, request, *args, **kwargs):
#         form = self.form_class(request.POST, account=self.request.user.userprofile)
#         if form.is_valid():
#             amount = form.cleaned_data.get('amount')
#             form.save()
#             messages.success(request, 'Deposit successful.')
#             mail_subject = "Money Deposited"
#             message = render_to_string('deposit_message.html', {
#                 'user': request.user,
#                 'amount': amount,
#             })
#             to_email = request.user.email
#             send_email = EmailMultiAlternatives(mail_subject, '', 'nasrullah9867@gmail.com', [to_email])
#             send_email.attach_alternative(message, "text/html")
#             send_email.send()
#             return redirect('home')
#         return render(request, self.template_name, {'form': form, 'title': self.title})



class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')
    
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        user = User.objects.create_user(
            username=username, 
            password=password, 
            email=email
        )
        UserAccount.objects.create(user=user, balance=0.00)
        return redirect('login')
    
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Logged in successfully as {username}")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'login.html')

class LogoutView(View):
    next_page = 'home'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(self.next_page)
        return redirect(self.next_page)

    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(request)
        return redirect(self.next_page)

class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transaction_report.html'
    model = Transaction
    balance = 0 # filter korar pore ba age amar total balance ke show korbe
    context_object_name = "transactions_report"

    def get_queryset(self):
        # jodi user filter na kre
        queryset = super().get_queryset().filter(account=self.request.user.account)
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

         # jodi user date filer kre
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(timestamp__date__range=(start_date, end_date))

            self.balance = Transaction.objects.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
        return queryset.distinct()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })
        return context
