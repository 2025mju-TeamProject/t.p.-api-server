# api/serializers.py

from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

from .models import Profile, ProfileImage
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password # Django 기본 비번 검증
from django.core.exceptions import ValidationError
from rest_framework.validators import UniqueValidator


# 1. 이미지 전용 시리얼라이저
class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileImage
        fields = ['id', 'image']

# 2. 프로필 관리용 시리얼라이저
class ProfileSerializer(serializers.ModelSerializer):
    """
    [GET, POST] 프로필 전체를 조회하거나 생성(AI 생성)할 때 사용함
    """
    images = ProfileImageSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        # 'user' 필드를 제외한 Profile 모델의 모든 필드를 다룹니다
        fields = [
            'nickname',
            'gender',
            'year', 'month', 'day', 'hour', 'minute',
            'birth_time_unknown',
            'location_city', 'location_district',
            'job', 'hobbies', 'mbti',
            'profile_text',
            'images'
        ]

class ProfileTextUpdateSerializer(serializers.ModelSerializer):
    """
    [PATCH] 사용자가 'profile_text' 필드 수정할 때 사용
    """
    class Meta:
        model = Profile
        fields = ['profile_text']

# 2. 회원가입/로그인용 시리얼라이저
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    회원가입을 위한 Serializer
    (ID, PW, PW 확인, 휴대폰 번호)
    """
    # 1. 'password'는 쓰기 전용, Django 기본 검증 통과해야함
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password] # Django의 기본 비밀번호 검증 적용
    )

    # 2. 'password_verify'는 검증용으로만 사용(DB에 안 쓰임)
    password_verify = serializers.CharField(
        write_only=True,
        required=True
    )
    phone_number = serializers.CharField(write_only=True, required=True, max_length=20)

    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="이미 등록된 아이디입니다."
            )
        ]
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'password_verify', 'phone_number')

    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("'-' 없이 11자리 숫자만 입력해 주세요.")

        if len(value) != 11:
            raise serializers.ValidationError("휴대폰 번호는 11자리여야 합니다.")

        return value

    def validate(self, data):
        """
        비밀번호 2개 일치 확인 (password vs password_verify)
        """
        if data['password'] != data['password_verify']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return data

    def create(self, validated_data):
        """
        검증 완료 후, 사용자를 생성하는 메서드
        """
        # DB에 저장되지 않는 password_verify 필드 제거함
        validated_data.pop('password_verify')
        phone_number = validated_data.pop('phone_number')

        # create_user()를 사용해야 해사로 저장됨
        user = User.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password']
        )

        try:
            profile = user.profile
            profile.phone_number = phone_number
            profile.save()
        except Profile.DoesNotExist:
            Profile.objects.create(user=user, phone_number=phone_number)

        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    SimpleJWT의 기본 로그인 시리얼라이즈 상속 -> 로그인 실패 메시지 한글화
    """

    def validate(self, attrs):
        try:
            # 1. SimpleJWT의 기본 로그인 검증 먼저 실행
            data = super().validate(attrs)

        except AuthenticationFailed as e:
            # 2. 기본 검증에서 로그인 실패 시,
            #    e.codes에 'no_activate_account'가 포함됨
            if hasattr(e, 'detail') and 'no_activate_account' in str(e.detail):
                raise AuthenticationFailed('아이디와 비밀번호가 일치하지 않습니다.')

            raise e

        return data