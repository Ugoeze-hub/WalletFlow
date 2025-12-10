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
    
    try:
        token = await oauth.google.authorize_access_token(request)
        
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(
                status_code=400, 
                detail="Failed to get user info from Google")
        
        user = db.query(User).filter(
            User.google_id == user_info['sub']
            ).first()
        
        if not user:            
            user = User(
                email=user_info['email'],
                google_id=user_info['sub'],
                name=user_info.get('name')
            )
            db.add(user)            
            db.commit()
            db.refresh(user)
            
            wallet = Wallet(
                user_id=user.id,
                wallet_number=str(uuid.uuid4().int)[:13]  
        )
            db.add(wallet)
            db.commit()
        
        access_token = create_access_token(user.id)
        
        return Token(access_token=access_token)

    except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Authentication failed: {str(e)}"
            )