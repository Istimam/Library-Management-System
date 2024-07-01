from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import datetime
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from .models import Book, Category, Review, Transaction, User, UserAccount
from .forms import ReviewForm, BookForm, CategoryForm, DepositForm
from django.views.generic import ListView, DetailView, FormView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .constants import DEPOSIT, BORROW, RETURN
    
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

class BookDetailView(DetailView):
    model = Book
    template_name = 'book_detail.html'
    context_object_name = 'book'
    form_class = ReviewForm

    def get_success_url(self):
        return reverse_lazy('book_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = Review.objects.filter(book=self.object)
        context['review_form'] = self.form_class()
        context['form'] = self.form_class()
        context['categories'] = self.object.category.all()
        if self.request.user.is_authenticated:
            context['user_account'] = UserAccount.objects.filter(user=self.request.user).first()
            context['user_borrowed'] = self.object.borrowers.filter(id=self.request.user.id).exists()
        else:
            context['user_account'] = None
            context['user_borrowed'] = False
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST)
        if form.is_valid():
            if request.user.is_authenticated:
                if self.object.borrowers.filter(id=request.user.id).exists():
                    review = form.save(commit=False)
                    review.book = self.object
                    review.user = request.user.useraccount  # Assign the user account to review
                    review.save()
                    messages.success(request, 'Review added successfully!')
                    return redirect('book_detail', pk=self.object.pk)
                else:
                    messages.error(request, 'You can only review books you have borrowed.')
            else:
                messages.error(request, 'You need to be logged in to add a review.')
                return redirect('login')

        if 'borrow' in request.POST:
            return self.borrow_book(request)
        elif 'return' in request.POST:
            return self.return_book(request)
        else:
            messages.error(request, 'Invalid request.')
            return self.render_to_response(self.get_context_data(form=form))

    def borrow_book(self, request):
        book = self.object
        user = request.user
        if not user.is_authenticated:
            messages.error(request, 'You need to be logged in to borrow books.')
            return redirect('book_detail', pk=book.pk)

        user_account = UserAccount.objects.filter(user=user).first()

        if not user_account:
            messages.error(request, 'You need a library account to borrow books. Please create an account.')
            return redirect('book_detail', pk=book.pk)

        if user_account.balance < book.borrowing_price:
            messages.error(request, 'You do not have enough balance to borrow this book.')
            return redirect('book_detail', pk=book.pk)

        user_account.balance -= Decimal(str(book.borrowing_price))
        user_account.save()

        Transaction.objects.create(
            account=user_account,
            book=book,
            amount=book.borrowing_price,
            balance_after_transaction=user_account.balance,
            transaction_type=BORROW
        )
        book.borrowers.add(user)
        messages.success(request, 'Book borrowed successfully!')
        mail_subject = "Book is borrowed"
        message = render_to_string('borrow_message.html', {
            'user': self.request.user,
            'book': book,
            'amount': book.borrowing_price,
        })
        to_email = self.request.user.email
        send_email = EmailMultiAlternatives(mail_subject, '', to=[to_email])
        send_email.attach_alternative(message, "text/html")
        send_email.send()
        return redirect('book_detail', pk=book.pk)

    def return_book(self, request):
        book = self.object
        user = request.user
        if not user.is_authenticated:
            messages.error(request, 'You need to be logged in to return books.')
            return redirect('book_detail', pk=book.pk)

        user_account = UserAccount.objects.filter(user=user).first()

        user_account.balance += Decimal(str(book.borrowing_price))
        user_account.save()

        Transaction.objects.create(
            account=user_account,
            book=book,
            amount=book.borrowing_price,
            balance_after_transaction=user_account.balance,
            transaction_type=RETURN
        )

        book.borrowers.remove(user)
        messages.success(request, 'Book returned successfully!')
        return redirect('book_detail', pk=book.pk)

    def form_valid(self, form):
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

class ProfileView(LoginRequiredMixin, ListView):
    template_name = 'profile.html'
    context_object_name = 'borrowed_books'
    paginate_by = 10

    def get_queryset(self):
        category_name = self.request.GET.get('category')
        if category_name:
            queryset = Book.objects.filter(borrowers=self.request.user, category__name=category_name)
        else:
            queryset = Book.objects.filter(borrowers=self.request.user)
        return queryset.order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        borrowed_categories = Category.objects.filter(book__borrowers=self.request.user).distinct()

        context.update({
            'borrowed_categories': borrowed_categories,
        })
        return context


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
        # Send email with transaction details
        send_transaction_mail(self.request.user, amount, "Deposit Message", "deposite_message.html")

        return super().form_valid(form)

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
    context_object_name = "transactions_report"
    balance = 0

    def get_queryset(self):
        queryset = super().get_queryset().filter(account=self.request.user.useraccount)
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(time__range=(start_date, end_date))

            self.balance = queryset.aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.useraccount.balance
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.useraccount,
            'balance': self.balance
        })
        return context
