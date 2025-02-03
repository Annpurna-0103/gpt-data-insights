from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

# Custom UserCreationForm to include the email field
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=40)  # Email field

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    # Override save method to save email as well
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']  # Assign email to user
        if commit:
            user.save()  # Save the user to the database
        return user

    # Custom validation for username uniqueness
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():  # Check if username already exists
            raise ValidationError("This username is already taken. Please choose a different one.")
        # Check if username follows the allowed pattern (e.g., starts with a letter and only allows underscores)
        if not username[0].isalpha():
            raise ValidationError("Username must start with an alphabetic character.")
        if not all(c.isalnum() or c == '_' for c in username):
            raise ValidationError("Username can only contain letters, digits, and underscores.")
        return username

    # Custom validation for email uniqueness
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():  # Check if email already exists
            raise ValidationError("This email is already associated with another account.")
        
        # Validate email format (basic)
        try:
            EmailValidator()(email)  # Using Django's built-in EmailValidator
        except ValidationError:
            raise ValidationError("Please enter a valid email address.")
        
        return email
    
    # Custom validation for password matching
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 != password2:
            raise ValidationError("Passwords do not match.")
        
        # Add additional password strength checks if necessary
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        return password2

class EditProfileForm(forms.ModelForm):
    # Fields for the User model
    class Meta:
        model = User
        fields = ['username', 'email']  # Only include username and email from the User model

    # Fields for the Profile model (additional details)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    profile_picture = forms.ImageField(required=False)

    # Fields for changing password (optional)
    old_password = forms.CharField(widget=forms.PasswordInput, required=False, label='Old Password')
    new_password = forms.CharField(widget=forms.PasswordInput, required=False, label='New Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False, label='Confirm New Password')

    def save(self, user, commit=True):
        # Save the User fields
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()

        # Save the Profile fields
        user_profile = user.profile
        user_profile.bio = self.cleaned_data['bio']
        user_profile.phone_number = self.cleaned_data['phone_number']
        if self.cleaned_data['profile_picture']:
            user_profile.profile_picture = self.cleaned_data['profile_picture']
        
        if commit:
            user_profile.save()

        # Handle password change if provided
        if self.cleaned_data['old_password'] and self.cleaned_data['new_password'] and self.cleaned_data['confirm_password']:
            # Check if the old password is correct
            if not user.check_password(self.cleaned_data['old_password']):
                raise forms.ValidationError('The old password is incorrect.')
            
            # Check if new passwords match
            if self.cleaned_data['new_password'] != self.cleaned_data['confirm_password']:
                raise forms.ValidationError('The new passwords do not match.')

            # Set the new password
            user.set_password(self.cleaned_data['new_password'])
            user.save()

        return user