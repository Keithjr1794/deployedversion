from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Book, Genre
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView
from .forms import LoanBookForm
from .models import Book, Author, BookInstance, Genre


@login_required
def index(request):
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    # If your index template is at: catalog/templates/catalog/index.html
    return render(request, 'catalog/index.html', context)


class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book


class BookDetailView(LoginRequiredMixin, generic.DetailView):
    model = Book


class AuthorListView(LoginRequiredMixin, generic.ListView):
    model = Author


class AuthorDetailView(LoginRequiredMixin, generic.DetailView):
    model = Author


class AuthorCreate(LoginRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death', 'author_image']

    def form_valid(self, form):
        author = form.save()
        return HttpResponseRedirect(reverse('catalog:author_list'))


class AuthorUpdate(LoginRequiredMixin, UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death', 'author_image']

    def form_valid(self, form):
        author = form.save()
        return HttpResponseRedirect(reverse('catalog:author_list'))


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # /accounts/login/
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Books on loan to the current user."""
    model = BookInstance
    template_name = 'catalog/my_books.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects
            .filter(borrower=self.request.user, status__exact='o')
            .order_by('due_back')
        )


def author_delete(request, pk):
    author = get_object_or_404(Author, pk=pk)
    try:
        author.delete()
        messages.success(request, f"{author.first_name} {author.last_name} has been deleted")
    except Exception:
        messages.success(
            request,
            f"{author.first_name} {author.last_name} cannot be deleted. Books exist for this author"
        )
    return redirect('catalog:author_list')


class AvailBooksListView(LoginRequiredMixin, generic.ListView):
    """List all available BookInstances."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_available.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='a').order_by('book__title')


def loan_book_librarian(request, pk):
    """Loan a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = LoanBookForm(request.POST, instance=book_instance)
        if form.is_valid():
            book_instance = form.save(commit=False)
            book_instance.due_back = datetime.date.today() + datetime.timedelta(weeks=4)
            book_instance.status = 'o'
            book_instance.save()
            return HttpResponseRedirect(reverse('catalog:all_available'))
    else:
        form = LoanBookForm(
            instance=book_instance,
            initial={'book_title': book_instance.book.title if book_instance.book else ''}
        )

    return render(request, 'catalog/loan_book_librarian.html', {'form': form})

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser
class BookCreate(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'book_image']

    def form_valid(self, form):
        post = form.save(commit=False)
        post.save()


        for genre in form.cleaned_data['genre']:
            theGenre = get_object_or_404(Genre, name=genre)
            post.genre.add(theGenre)

        post.save()
        return HttpResponseRedirect(reverse('catalog:book_list'))

class BookUpdate(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'book_image']
    template_name = 'catalog/book_form.html'

    def form_valid(self, form):
        post = form.save(commit=False)


        for genre in post.genre.all():
            post.genre.remove(genre)

        post.save()


        for genre in form.cleaned_data['genre']:
            theGenre = get_object_or_404(Genre, name=genre)
            post.genre.add(theGenre)

        post.save()
        return HttpResponseRedirect(reverse('catalog:book_list'))

def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    try:
        book.delete()
        messages.success(request, f"{book.title} has been deleted")
    except:
        messages.success(request, f"{book.title} cannot be deleted")
    return redirect('catalog:book_list')

class BookDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    template_name = "catalog/book_confirm_delete.html"
    success_url = reverse_lazy("catalog:book_list")

    def test_func(self):
        return self.request.user.is_superuser

