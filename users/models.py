from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Helps Django work with our custom user model"""

    use_in_migrations = True

    def create_user(self, name, email, password=None):
        """Creates a new user objects"""

        if not email:
            raise ValueError('Users must have an email address')

        if not name:
            raise ValueError('Users must have names')

        email = self.normalize_email(email.lower())
        name = name.strip()
        user = self.model(name=name, email=email)
        user.set_password(password)
        user.save(using=self._db)

        return user


class User(AbstractBaseUser):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    date = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    from_user = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = [('from_user', 'to_user'), ('to_user', 'from_user')]

    def save(self, *args, **kwargs):
        if FriendRequest.objects.filter(from_user=self.to_user, to_user=self.from_user).exists():
            raise ValueError("A friend request already exists from the recipient to the sender")
        super().save(*args, **kwargs)

