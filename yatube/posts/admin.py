from django.contrib import admin
from django.conf import settings

from .models import Post, Group, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group',)
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = settings.EMPTY_VALUE


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'slug', 'description',)
    search_fields = ('title',)
    empty_value_display = settings.EMPTY_VALUE


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'post', 'author', 'created')
    search_fields = ('text',)
    empty_value_display = settings.EMPTY_VALUE


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
