# Register your models here.
from django.contrib import admin
from .models import DataFile, Insight, Portfolio, Profile, DownloadLog
from django.contrib.auth.models import User

# Profile Admin: Profile picture aur bio ko display karne ke liye
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_picture', 'bio', 'phone_number')
    search_fields = ('user__username', 'user__email', 'bio')
    list_filter = ('user__is_active',)

# DataFile Admin: File information aur user ke saath link
class DataFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'user', 'uploaded_at', 'processed', 'file_hash')
    search_fields = ('file__name', 'user__username', 'description')
    list_filter = ('processed', 'uploaded_at')

     # Add a custom field to show the number of downloads
    def download_count(self, obj):
        return DownloadLog.objects.filter(file=obj).count()
    download_count.short_description = 'Downloads'
   
    # Add the download count to the list display
    list_display = ('file', 'user', 'uploaded_at', 'processed', 'file_hash', 'download_count')

class InsightAdmin(admin.ModelAdmin):
    # Update this to only include valid fields
    list_display = ('prompt', 'response', 'generated_at')  # No 'data_file' anymore
    search_fields = ('prompt', 'response')
    list_filter = ('generated_at',)  # Optionally filter by 'generated_at'


class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'data_file', 'created_at', 'tags')
    search_fields = ('user__username', 'data_file__file__name', 'tags')
    list_filter = ('created_at',)

# Admin view for DownloadLog
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'downloaded_at')
    search_fields = ('user__username', 'file__file__name')
    list_filter = ('downloaded_at',)

# Register the model with the admin site
admin.site.register(DownloadLog, DownloadLogAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(DataFile, DataFileAdmin)
admin.site.register(Insight, InsightAdmin)
admin.site.register(Portfolio, PortfolioAdmin)

# Optionally, you can register the User model as well, if you want to customize it further
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)  # Only if you want to customize built-in User admin

