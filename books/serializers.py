from rest_framework import serializers
from .models import Book, BorrowRecord


class BookSerializer(serializers.ModelSerializer):
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "published_date",
            "total_copies",
            "available_copies",
            "is_available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_available", "created_at", "updated_at"]

    def get_is_available(self, obj):
        return getattr(obj, "available_copies", 0) > 0

    def validate(self, attrs):
        # Support both full POST/PUT and partial PATCH updates
        total_copies = attrs.get(
            "total_copies",
            getattr(self.instance, "total_copies", 1),
        )
        available_copies = attrs.get(
            "available_copies",
            getattr(self.instance, "available_copies", total_copies),
        )

        if total_copies < 0:
            raise serializers.ValidationError(
                {"total_copies": "Total copies cannot be negative."}
            )
        if available_copies < 0:
            raise serializers.ValidationError(
                {"available_copies": "Available copies cannot be negative."}
            )
        if available_copies > total_copies:
            raise serializers.ValidationError(
                {
                    "available_copies": "Available copies cannot exceed total copies."
                }
            )
        return attrs

class BorrowRecordSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(read_only=True)
    book_isbn = serializers.CharField(source="book.isbn", read_only=True)
    member_username = serializers.CharField(source="member.username", read_only=True)
    issued_by_username = serializers.CharField(
        read_only=True, default=None
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = BorrowRecord
        fields = [
            "id",
            "book",
            "book_title",
            "book_isbn",
            "member",
            "member_username",
            "issued_by",
            "issued_by_username",
            "borrowed_at",
            "due_date",
            "returned_at",
            "status",
            "is_overdue",
        ]
        read_only_fields = [
            "id",
            "issued_by",
            "borrowed_at",
            "returned_at",
            "status",
            "is_overdue",
        ]