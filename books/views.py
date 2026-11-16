from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsLibrarian, IsLibrarianOrReadOnly
from .models import Book, BorrowRecord
from .serializers import BookSerializer, BorrowRecordSerializer
from rest_framework.permissions import IsAuthenticated

class BookListCreateAPIView(APIView):
    """
    GET: Any authenticated user can list/search books.
    POST: Only Librarians can add new books.
    """
    permission_classes = [IsLibrarianOrReadOnly]

    def get(self, request):
        books = Book.objects.all().order_by("-id")
        
        # Optional search query parameter (?search=harry)
        search_query = request.query_params.get("search")
        if search_query:
            books = books.filter(
                Q(title__icontains=search_query)
                | Q(author__icontains=search_query)
                | Q(isbn__icontains=search_query)
            )

        serializer = BookSerializer(books, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailAPIView(APIView):
    """
    GET: Any authenticated user can view book details.
    PUT / PATCH / DELETE: Only Librarians can modify or remove books.
    """
    permission_classes = [IsLibrarianOrReadOnly]

    def get_object(self, pk):
        return get_object_or_404(Book, pk=pk)

    def get(self, request, pk):
        book = self.get_object(pk)
        serializer = BookSerializer(book)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        book = self.get_object(pk)
        serializer = BookSerializer(book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        book = self.get_object(pk)
        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        book = self.get_object(pk)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BorrowRecordListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_librarian = (
            getattr(user, "role", None) == "LIBRARIAN"
            or user.is_staff
            or user.is_superuser
        )

        queryset = BorrowRecord.objects.select_related("book", "member", "issued_by")

        if not is_librarian:
            queryset = queryset.filter(member=user)
        else:
            member_id = request.query_params.get("member_id")
            if member_id:
                queryset = queryset.filter(member_id=member_id)

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        serializer = BorrowRecordSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IssueBookAPIView(APIView):
    """
    POST: Librarian issues a book to a member.
    Decrements available_copies atomically.
    """
    permission_classes = [IsLibrarian]

    def post(self, request):
        serializer = BorrowRecordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        book_id = serializer.validated_data["book"].id
        member = serializer.validated_data["member"]

        with transaction.atomic():
            # Lock the book row until the transaction finishes
            book = Book.objects.select_for_update().get(pk=book_id)

            if book.available_copies < 1:
                return Response(
                    {"detail": "No copies of this book are currently available."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prevent the same member from borrowing two copies of the same book simultaneously
            already_borrowed = BorrowRecord.objects.filter(
                book=book,
                member=member,
                status=BorrowRecord.Status.BORROWED,
            ).exists()

            if already_borrowed:
                return Response(
                    {"detail": "This member already has an active loan for this book."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            book.available_copies -= 1
            book.save(update_fields=["available_copies", "updated_at"])

            borrow_record = serializer.save(
                issued_by=request.user,
                status=BorrowRecord.Status.BORROWED,
            )

        return Response(
            BorrowRecordSerializer(borrow_record).data,
            status=status.HTTP_201_CREATED,
        )


class ReturnBookAPIView(APIView):
    """
    POST: Librarian marks a borrowed record as returned.
    Increments available_copies atomically.
    """
    permission_classes = [IsLibrarian]

    def post(self, request, pk):
        with transaction.atomic():
            borrow_record = get_object_or_404(
                BorrowRecord.objects.select_for_update(),
                pk=pk,
            )

            if borrow_record.status == BorrowRecord.Status.RETURNED:
                return Response(
                    {"detail": "This book has already been returned."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            book = Book.objects.select_for_update().get(pk=borrow_record.book_id)

            # Safely increment available_copies without exceeding total_copies
            if book.available_copies < book.total_copies:
                book.available_copies += 1
                book.save(update_fields=["available_copies", "updated_at"])

            borrow_record.status = BorrowRecord.Status.RETURNED
            borrow_record.returned_at = timezone.now()
            borrow_record.save(update_fields=["status", "returned_at"])

        return Response(
            BorrowRecordSerializer(borrow_record).data,
            status=status.HTTP_200_OK,
        )