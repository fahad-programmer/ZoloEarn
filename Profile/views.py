from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import UserSerializer
from django.contrib.auth import authenticate, login, get_user_model
from rest_framework.decorators import api_view, action
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework import viewsets, permissions

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            if User.objects.filter(email=request.data['email']).exists():
                return Response({"message":"Email Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
        except IntegrityError:
            return Response({"message": "Username or email is already in use"}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response({"message":"Invalid Data Check Your Input Please"})

        # Generate a token for the newly created user
        user = User.objects.get(pk=serializer.data['id'])
        token, created = Token.objects.get_or_create(user=user)

        # Return the token in the response
        return Response({'token': token.key}, status=status.HTTP_201_CREATED, headers=headers)


    def login(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        else:
            return Response({"message":"Username Or Password Is Incorrect"},status=status.HTTP_401_UNAUTHORIZED)
