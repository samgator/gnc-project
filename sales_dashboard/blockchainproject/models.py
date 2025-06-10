from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, username, phone_number, member_name, wallet_address, password=None):
        if not username:
            raise ValueError("Users must have a username")
        user = self.model(
            username=username,
            phone_number=phone_number,
            member_name=member_name,
            wallet_address=wallet_address,
            date_joined=timezone.now()
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, phone_number, member_name, wallet_address, password):
        user = self.create_user(
            username=username,
            phone_number=phone_number,
            member_name=member_name,
            wallet_address=wallet_address,
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    phone_number = models.CharField(max_length=20)
    member_name = models.CharField(max_length=150)
    wallet_address = models.CharField(max_length=100, unique=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number', 'member_name', 'wallet_address']

    def __str__(self):
        return self.username
