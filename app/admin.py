"""
Django Admin Configuration
Tương đương với Laravel Nova (admin panel)

Django admin tự động generate từ models - rất mạnh và miễn phí!
"""

from django.contrib import admin
from .models import Document, DocumentChunk, ChatMessage


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Document admin - tương đương với Laravel Nova Document resource"""
    list_display = ['name', 'status', 'num_chunks', 'user', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'path']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'path', 'user', 'status')
        }),
        ('Processing Information', {
            'fields': ('num_chunks', 'embedding_model', 'processed_at', 'error_message')
        }),
        ('File Information', {
            'fields': ('file_size', 'file_hash')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """DocumentChunk admin"""
    list_display = ['id', 'document', 'content_preview', 'created_at']
    list_filter = ['created_at', 'document']
    search_fields = ['content', 'document__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """ChatMessage admin"""
    list_display = ['id', 'user', 'role', 'content_preview', 'document', 'created_at']
    list_filter = ['role', 'created_at', 'document']
    search_fields = ['content', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:30] + "..." if len(obj.content) > 30 else obj.content
    content_preview.short_description = 'Content'

