from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'status', 'first_name', 'password', 'last_name')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(_("This username is already in use."))
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            rank=validated_data.get('status', None),
            sector=validated_data.get('first_name', None),
        )        
        if validated_data.get('last_name'):
            user.photo = validated_data.get('last_name')
        user.set_password(validated_data['password'])
        user.save()
        return user
    
    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.status = validated_data.get('status', instance.status)
        instance.username = validated_data.get('username', instance.username)

        
        instance.save()
        return instance



class MyOwnSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user) -> Token:
        token =  super().get_token(user)
        token['username'] = user.username
        if user.status:
            token['status'] = user.status
        token['photo'] = user.photo.url
        token['id'] = user.id
        return token
    def validate(self, attrs):
        data = super().validate(attrs)
        data['id'] = self.user.id
        data['username'] = self.user.username
        if self.user.status:
            data['status'] = self.user.status
        data['photo'] = self.user.photo.url       
        return data
