from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import User, FriendRequest

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','name','email','date','password']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.save()
        return user

class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'timestamp', 'status']