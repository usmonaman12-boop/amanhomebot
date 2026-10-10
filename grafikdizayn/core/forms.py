from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Group, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "input", "autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input"}))


class TeacherCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input"}), label="Parol")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "phone", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "input"}),
            "first_name": forms.TextInput(attrs={"class": "input"}),
            "last_name": forms.TextInput(attrs={"class": "input"}),
            "phone": forms.TextInput(attrs={"class": "input"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_TEACHER
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "input", "placeholder": "Guruh nomi"})}


class StudentCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input"}), label="Parol")
    father_phone = forms.CharField(
        required=False, max_length=20, label="Otasining raqami",
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "+998 90 123 45 67"}),
    )
    mother_phone = forms.CharField(
        required=False, max_length=20, label="Onasining raqami",
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "+998 90 123 45 67"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "phone", "password"]
        labels = {"phone": "O'quvchining o'z raqami"}
        widgets = {
            "username": forms.TextInput(attrs={"class": "input", "placeholder": "login"}),
            "first_name": forms.TextInput(attrs={"class": "input", "placeholder": "Ism"}),
            "last_name": forms.TextInput(attrs={"class": "input", "placeholder": "Familiya"}),
            "phone": forms.TextInput(attrs={"class": "input", "placeholder": "+998 90 123 45 67"}),
        }

    def clean(self):
        cleaned = super().clean()
        phones = [cleaned.get("phone"), cleaned.get("father_phone"), cleaned.get("mother_phone")]
        if not any((p or "").strip() for p in phones):
            raise forms.ValidationError(
                "Kamida bitta telefon raqam kiriting (o'quvchining o'zi, otasi yoki onasi)."
            )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.ROLE_STUDENT
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
