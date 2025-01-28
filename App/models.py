# App/models.py
from django.db import models

class GymCard(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
        ('deactivated', 'Deactivated'),
        ('suspended', 'Suspended')
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.IntegerField(default=0)
    is_expired = models.BooleanField(default=False)

    def __str__(self):
        return self.title
