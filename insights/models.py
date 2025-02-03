from django.db import models
import hashlib
from django.conf import settings
from django.contrib.auth.models import User  # Using built-in User model

# Profile Model (to store extra details like profile pic)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)  # Short bio for the user
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

# DataFile Model
class DataFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    processed = models.BooleanField(default=False)
    columns_info = models.JSONField(blank=True, null=True)
    file_hash = models.CharField(max_length=64, unique=True, editable=False)

    def save(self, *args, **kwargs):
        # Validate file size (10 MB limit)
        if self.file.size > 10 * 1024 * 1024:
            raise ValueError("The maximum file size allowed is 10 MB.")
        
        # Validate file type (only .csv allowed)
        if not self.file.name.endswith('.csv'):
            raise ValueError("Only CSV files are allowed.")
        
        # Calculate file hash to avoid duplicate uploads
        hasher = hashlib.sha256()
        for chunk in self.file.chunks():
            hasher.update(chunk)
        self.file_hash = hasher.hexdigest()
        
        super(DataFile, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.file.name} uploaded by {self.user.username}"

class DownloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} downloaded {self.file.file.name} at {self.downloaded_at}"
    
# Insight Model
class Insight(models.Model):
   
    generated_at = models.DateTimeField(auto_now_add=True)
    prompt = models.TextField()  # The GPT prompt used for generating insight
    response = models.TextField()  # The GPT-generated response
    prediction = models.JSONField(blank=True, null=True)  # Prediction or forecast data if any

    def __str__(self):
        # Just use the prompt and the generated_at timestamp for simplicity
        return f"Insight: {self.prompt[:50]}... at {self.generated_at}"  # Truncate prompt if it's too long

# Portfolio Model
class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE)
    insights_summary = models.TextField()  # Summary of insights for portfolio display
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=100, blank=True)  # Tags for easy filtering and search

    def __str__(self):
        return f"Portfolio item for {self.user.username} - {self.data_file.file.name}"
