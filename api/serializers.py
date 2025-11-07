# api/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password # Django 기본 비번 검증
from django.core.exceptions import ValidationError

class UserRegistrationSerialzer(serializers.ModelSerializer):
    """
    회원갇입을 위한 Serializer
    (ID, PW, PW 확인)
    """

    # 1. 'password'는 쓰기 전용으로 설정
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password] # Django의 기본 비밀번호 검증 적용
    )

    # 2. 'password_verify'는 DB에 쓰이지 않고 검증용으로만 사용
    password_verify = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'password_verify')

    def validate_username(selfself, value):
        """
        ID(username) 중복 확인
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 등록된 아이디입니다.")
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
        검증(validate) 완료 후, 사용자를 생성(create)하는 메서드
        """
        # DB에 저장되지 않는 password_verify 필드 제거함
        validated_data.pop('password_verify')

        # create_user()를 사용해야 해사로 저장됨
        user = User.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password']
        )
        return user