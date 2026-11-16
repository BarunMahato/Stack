from django.urls import path
from .views import (
    BookDetailAPIView,
    BookListCreateAPIView,
    BorrowRecordListAPIView,
    IssueBookAPIView,
    ReturnBookAPIView,
)

app_name = "books"

urlpatterns = [
    # Book Catalog Endpoints
    path("", BookListCreateAPIView.as_view(), name="book-list-create"),
    path("<int:pk>/", BookDetailAPIView.as_view(), name="book-detail"),

    # Borrow / Return Transaction Endpoints
    path("transactions/", BorrowRecordListAPIView.as_view(), name="transaction-list"),
    path("transactions/issue/", IssueBookAPIView.as_view(), name="book-issue"),
    path(
        "transactions/<int:pk>/return/",
        ReturnBookAPIView.as_view(),
        name="book-return",
    ),
]