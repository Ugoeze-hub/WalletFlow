from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.google_oauth import oauth
from app.auth.jwt_auth import create_access_token
from app.models.user import User
from app.models.wallet import Wallet
import uuid
from app.schemas.user import Token
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/google")
async def google_login(request: Request):
    redirect_uri = await oauth.google.authorize_redirect(
        request, 
        settings.GOOGLE_REDIRECT_URI
    )
    return redirect_uri

@router.get("/google/callback")
async def google_callback(
    request: Request, 
    db: Session = Depends(get_db)
):
    
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    
    logger.info(f"Google OAuth callback received with code: {code} and error: {error}")
    
    if error:
        logger.error(f"Google OAuth error: {error}")
        raise HTTPException(
            status_code=400, 
            detail=f"Google authorization error"
        )
        
    if not code:
        logger.error("No code parameter found in the callback request")
        raise HTTPException(
            status_code=400, 
            detail="Missing authorization code. Please start login again."
        )
    
    try:
        logger.info("Exchanging code for token with Google")
        
        token = await oauth.google.authorize_access_token(request)
        
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(
                status_code=400, 
                detail="Failed to get user info from Google")
        
        logger.info(f"User info retrieved from Google: {user_info.get('email')}")
        
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