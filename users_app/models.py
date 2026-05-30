from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Менеджер для кастомной модели пользователя с email в качестве логина"""
    
    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        
        # Если username не указан, используем часть email до @
        if username is None:
            username = email.split('@')[0]
        
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')
        
        # Для суперпользователя создаём username из email (без домена)
        username = email.split('@')[0]
        
        return self.create_user(email=email,
            username=username,
            password=password,
            **extra_fields)

  
class User(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя с email в качестве логина и опциональным username"""
    
    email = models.EmailField(unique=True, verbose_name='Email')
    username = models.CharField(
        max_length=150, 
        unique=True, 
        blank=True, 
        null=True, 
        verbose_name='Имя пользователя'
    )
    
    is_staff = models.BooleanField(default=False, verbose_name='Статус персонала')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_superuser = models.BooleanField(default=False, verbose_name='Суперпользователь')
    
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Дата регистрации')
    last_login = models.DateTimeField(blank=True, null=True, verbose_name='Последний вход')
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email уже обязателен, username опционален
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.email
    
    def get_username(self):
        """Возвращает username или email, если username не задан"""
        return self.username if self.username else self.email