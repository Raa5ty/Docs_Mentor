from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Форма создания пользователя в админке"""
    
    email = forms.EmailField(label='Email', required=True)
    
    class Meta:
        model = User
        fields = ('email', 'username')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким Email уже существует.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Явно устанавливаем email из поля формы
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """Форма изменения пользователя в админке"""
    
    email = forms.EmailField(label='Email', required=True)
    
    class Meta:
        model = User
        fields = '__all__'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Проверяем, что email не занят другим пользователем
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Пользователь с таким Email уже существует.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для кастомной модели пользователя"""
    
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('id', 'email', 'username', 'is_staff', 'is_active')
    list_display_links = ('id', 'email')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'username')
    ordering = ('id',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )