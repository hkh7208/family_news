from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import FamilyMemberPhoto, FamilyMemberProfile, FamilyPost, FamilyPostImage, FamilyPostVideo, Tag


class FamilyMemberProfileInline(admin.StackedInline):
	model = FamilyMemberProfile
	can_delete = False
	extra = 0
	verbose_name_plural = '가족 구성원 프로필'


class FamilyMemberPhotoInline(admin.TabularInline):
	model = FamilyMemberPhoto
	extra = 1
	fields = ('image', 'caption', 'created_at')
	readonly_fields = ('created_at',)
	verbose_name_plural = '가족 개인 사진'


class FamilyUserAdmin(UserAdmin):
	inlines = (FamilyMemberProfileInline, FamilyMemberPhotoInline)


@admin.register(FamilyPost)
class FamilyPostAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'is_hero', 'created_at')
	list_filter = ('is_hero', 'created_at')
	search_fields = ('title', 'content', 'author__username')
	filter_horizontal = ('tags',)
	inlines = []


class FamilyPostImageInline(admin.TabularInline):
	model = FamilyPostImage
	extra = 1
	fields = ('image', 'created_at')
	readonly_fields = ('created_at',)


class FamilyPostVideoInline(admin.TabularInline):
	model = FamilyPostVideo
	extra = 1
	fields = ('video', 'created_at')
	readonly_fields = ('created_at',)


FamilyPostAdmin.inlines = [FamilyPostImageInline, FamilyPostVideoInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(FamilyPostImage)
class FamilyPostImageAdmin(admin.ModelAdmin):
	list_display = ('post', 'created_at')
	list_filter = ('created_at',)
	search_fields = ('post__title',)


@admin.register(FamilyPostVideo)
class FamilyPostVideoAdmin(admin.ModelAdmin):
	list_display = ('post', 'created_at')
	list_filter = ('created_at',)
	search_fields = ('post__title',)


@admin.register(FamilyMemberPhoto)
class FamilyMemberPhotoAdmin(admin.ModelAdmin):
	list_display = ('user', 'caption', 'created_at')
	list_filter = ('created_at', 'user')
	search_fields = ('user__username', 'caption')


try:
	admin.site.unregister(User)
except admin.sites.NotRegistered:
	pass

admin.site.register(User, FamilyUserAdmin)
