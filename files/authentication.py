from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTAuthenticationFromQuery(JWTAuthentication):
    """
    Custom JWT Authentication that supports token from URL query parameter
    This is useful for file downloads and iframe integration
    """

    def authenticate(self, request):
        # CORS preflight (OPTIONS) uchun autentifikatsiya kerak emas
        if request.method == 'OPTIONS':
            return None

        # 1. Avval query parametrdan tokenni olishga harakat qilish
        token = request.query_params.get('token')

        if token:
            try:
                # Tokenni validatsiya qilish
                validated_token = self.get_validated_token(token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except Exception as e:
                raise AuthenticationFailed(
                    'Noto\'g\'ri yoki muddati o\'tgan token. Iltimos, qayta login qiling.')

        # 2. Agar query parametrda token bo'lmasa, Authorization headerdan olish
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        # 3. Agar hech qanday token topilmasa
        raise AuthenticationFailed(
            'JWT token topilmadi. Iltimos, token yuboring.')
