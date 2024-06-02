from django.db import IntegrityError
from django.forms import ValidationError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, FriendRequestSerializer
from .models import User, FriendRequest
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework.throttling import UserRateThrottle
from rest_framework.decorators import throttle_classes

class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


class SendFriendRequestThrottle(UserRateThrottle):
    scope = 'send_friend_request'
    rate= '3/minute'


class UserViewSet(viewsets.ViewSet):
    pagination_class = UserPagination

    @action(detail=False, methods=['post'])
    def signup(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response({'message': "You have been successfully registered "}, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({'error': "Email address is already in use"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'],)
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)
        if not user:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_404_NOT_FOUND)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication credentials were not provided.")

        search_keyword = request.query_params.get('query', '')

        if not search_keyword:
            raise ValidationError("Search query cannot be empty")

        if '@' in search_keyword:
            try:
                user = User.objects.get(email=search_keyword)
                serializer = UserSerializer(user)
                return Response(serializer.data)
            except user.DoesNotExist:
                return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        else:
            users = User.objects.filter(
                name__icontains=search_keyword
            )
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(users, request)
            serializer = UserSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], throttle_classes=[SendFriendRequestThrottle])
    def send_friend_request(self, request):
        
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication credentials were not provided.")
        
        to_user_email = request.data.get('email')
        if not to_user_email:
            return Response({'error': 'Email is required to send a friend request'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            to_user = User.objects.get(email__iexact=to_user_email)
            if to_user == request.user:
                return Response({'error': 'You cannot send a friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if FriendRequest.objects.filter(Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user)).exists():
            return Response({'error': 'Friend request already exists'}, status=status.HTTP_400_BAD_REQUEST)

        friend_request = FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        return Response({'message': 'Friend request sent successfully'}, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def respond_friend_request(self, request):
        
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication credentials were not provided.")
         
        request_id = request.data.get('request_id')
        request_status = request.data.get('status')
        
        if not request_id or request_status not in ['accepted', 'rejected']:
            return Response({'error': 'Request ID and a valid status ("accepted" or "rejected") are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user, status='pending')
            friend_request.status = request_status
            friend_request.save()
            return Response({'message': f'Friend request {request_status}'}, status=status.HTTP_200_OK)
        except FriendRequest.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def list_friends(self, request):
        
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication credentials were not provided.")

        friend_requests = FriendRequest.objects.filter(Q(from_user=request.user) | Q(to_user=request.user), status='accepted').values_list('from_user_id', 'to_user_id')
        print(friend_requests)
        
        user_ids = set()
        for from_user_id, to_user_id in friend_requests:
            user_ids.add(from_user_id)
            user_ids.add(to_user_id)
        user_ids.discard(request.user.id)
        friends = User.objects.filter(id__in=user_ids)
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(friends, request)
        serializer = UserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def list_pending_friend_requests(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication credentials were not provided.")
        
        # Get pending friend requests received by the current user
        pending_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
        
        # Serialize the pending friend requests
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(pending_requests, request)
        serializer = FriendRequestSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
