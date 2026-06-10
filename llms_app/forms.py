# llms_app/forms.py
from django import forms
from .models import UserAPIKey

class UserAPIKeyAdminForm(forms.ModelForm):
    new_api_key = forms.CharField(
        max_length=500,
        required=False,  # пока False, проверим в clean
        label="API ключ",
        widget=forms.PasswordInput(render_value=False)
    )

    class Meta:
        model = UserAPIKey
        fields = "__all__"
        exclude = ['api_key']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Редактирование существующего
            self.fields['new_api_key'].required = False
            self.fields['new_api_key'].help_text = "Ключ установлен. Введите новый API key, если нужно заменить текущий"
        else:
            # Создание нового
            self.fields['new_api_key'].required = True
            self.fields['new_api_key'].help_text = "Введите API ключ"

    def clean_new_api_key(self):
        value = self.cleaned_data.get('new_api_key')
        
        # При создании нового объекта ключ обязателен
        if not self.instance.pk and not value:
            raise forms.ValidationError("API ключ обязателен.")
        
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_key = self.cleaned_data.get('new_api_key')
        if new_key:
            instance.api_key = new_key
        if commit:
            instance.save()
        return instance
    
# Вариант только поле для нового ключа и без вывода старого в админке
# class UserAPIKeyAdminForm(forms.ModelForm):
#     new_api_key = forms.CharField(
#         max_length=500,
#         required=False,
#         label="API key",
#         help_text="Введите свой API key:",
#         widget=forms.PasswordInput(render_value=False)
#     )

#     class Meta:
#         model = UserAPIKey
#         fields = "__all__"
#         exclude = ['api_key']  # скрываем старое поле

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if self.instance.pk and self.instance.api_key:
#             self.fields['new_api_key'].help_text = "Ключ установлен. Введите новый API key, если нужно заменить текущий."

#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         new_key = self.cleaned_data.get('new_api_key')
#         if new_key:
#             instance.api_key = new_key
#         if commit:
#             instance.save()
#         return instance