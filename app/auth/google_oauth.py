from authlib.integrations.starlette_client import OAuth
from app.config import settings
import urllib.parse

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',
    }
)
def generate_google_auth_url() -> str:
    """
    Generate Google OAuth authorization URL for manual testing.
    
    This allows users to get the URL, open it in a browser,
    and manually copy the authorization code after login.
    
    Returns:
        str: Full Google OAuth authorization URL
    """
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    
    base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    query_string = urllib.parse.urlencode(params)
    
    return f"{base_url}?{query_string}"
