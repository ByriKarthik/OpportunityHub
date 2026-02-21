from django.db import models
from django.utils import timezone


class Opportunity(models.Model):
    SOURCE_CHOICES = [
        ('IIT', 'IIT'),
        ('IVY', 'Ivy League'),
    ]

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    opportunity_type = models.CharField(max_length=50, default="OTHER")
    deadline = models.DateField(null=True, blank=True)
    university = models.CharField(max_length=200)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    link = models.URLField(unique=True)
    posted_date = models.DateField(blank=True, null=True)
    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.university}"

    @property
    def deadline_status(self):
        if not self.deadline:
            return None
        days_left = (self.deadline - timezone.localdate()).days
        if days_left <= 7:
            return "CLOSING_SOON"
        if days_left <= 30:
            return "HURRY"
        return "OPEN"
