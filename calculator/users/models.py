from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    auth0_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    class Meta:
        ordering = ['-date_joined']
