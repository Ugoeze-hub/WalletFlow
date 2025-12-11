from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.google_oauth import oauth, generate_google_auth_url
from app.auth.jwt_auth import create_access_token
from app.models.user import User
from app.models.wallet import Wallet
import uuid
import httpx
from app.schemas.user import Token, GoogleAuthURL
from app.config import settings
import urllib.parse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/google")
async def google_login(request: Request):
    auth_url = generate_google_auth_url()
    
    logger.info(f"Generated Google OAuth URL")
    
    return GoogleAuthURL(
        authorization_url=auth_url,
        instructions="Open this URL in your browser, complete login, then copy the 'code' parameter from the redirect URL"
    )

@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google (from the redirect URL after login)"), 
    db: Session = Depends(get_db)
):
    try:
        
        code = urllib.parse.unquote(code)
        logger.info(f"Received code decoded: {code}")
        logger.info(f"Using redirect_uri: {settings.GOOGLE_REDIRECT_URI}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                'https://oauth2.googleapis.com/token',
                params={
                    'code': code,
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                    'grant_type': 'authorization_code'
                }
            )
        
        if token_response.status_code != 200:
            error_detail = token_response.json().get('error_description', 'Token exchange failed')
            raise HTTPException(status_code=400, detail=error_detail)
        
        token_data = token_response.json()
        logger.info(f"Token data received from Google")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            userinfo_response = await client.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f"Bearer {token_data['access_token']}"}
            )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = userinfo_response.json()
        
        google_id = user_info['sub']
        email = user_info['email']
        
        if not google_id:
            logger.error("Google ID (sub) missing from user info")
            raise HTTPException(
                status_code=400,
                detail="Google ID (sub) missing"
                )
        
        if not email:
            logger.error("Email missing from user info")
            raise HTTPException(
                status_code=400,
                detail="Email missing from Google response"
                )
        
        user = db.query(User).filter(
            User.google_id == google_id
            ).first()
        
        if not user:            
            user = User(
                email=email,
                google_id=google_id,
                name=user_info.get('name')
            )
            db.add(user)            
            db.commit()
            db.refresh(user)
            logger.info(f"New user created: {email}")
            
            wallet = Wallet(
                user_id=user.id,
                wallet_number=str(uuid.uuid4().int)[:13]  
        )
            db.add(wallet)
            db.commit()
            logger.info(f"New user wallet created: {email}")
            
        else:
            logger.info(f"Existing user found: {user.email}")
        
        try:
            access_token = create_access_token(
                user_id=str(user.id),
                user_email=user.email
            )
            logger.info(f"Access token created for user: {user.email}")
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create access token"
            )
        
        return Token(
            access_token=access_token,
            token_type="bearer"      
        )

    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Authentication failed: {str(e)}"
        )