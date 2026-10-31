from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class LoginSerializer(TokenObtainPairSerializer):    # extends the ready-made JWT login

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)               # let simplejwt build the normal token
        token["role"] = user.roleid.title             # store the role INSIDE the token
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)                # checks the username and password
        return {                                      # what the login response will contain
            "username": self.user.username,
            "role": self.user.roleid.title,
            "access": data["access"],                 # token sent with every request
            "refresh": data["refresh"],               # token used to get a new access token
        }


class LoginView(TokenObtainPairView):                 # the login endpoint
    serializer_class = LoginSerializer                # use our serializer above


def Roles(*roles):                                    # *roles collects all names into a tuple
    class RolePermission(BasePermission):             # a permission class built for those roles
        message = f"Access denied. Required roles: {', '.join(roles)}."   # text in the 403 response

        def has_permission(self, request, view):      # DRF calls this on every request
            user = request.user
            return bool(
                user
                and user.is_authenticated             # logged in 
                and user.roleid.title in roles        # and the role is one of the allowed ones
            )

    return RolePermission                             # give back the class