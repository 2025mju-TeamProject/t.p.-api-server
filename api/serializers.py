# api/serializers.py

from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

# from .models import Profile, ProfileImage
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password # Django 기본 비번 검증
from django.core.exceptions import ValidationError
from rest_framework.validators import UniqueValidator