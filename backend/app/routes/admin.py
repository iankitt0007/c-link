from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, constr
from supabase import Client
from db.supabase import get_supabase_admin_client
from typing import Optional
from enum import Enum
import os

router = APIRouter()
security = HTTPBearer()

# Role enum
class Role(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"

# Simplified Pydantic models
class UserSignup(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=8)] = None

# JWT validation dependency with role check (reused from auth.py)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        supabase = get_supabase_client()  # Assuming get_supabase_client is imported
        user = supabase.auth.get_user(token)
        
        if not user.user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
        return user.user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Admin or Superadmin dependency
async def get_admin_user(current_user: dict = Depends(get_current_user)):
    user_role = current_user.user_metadata.get("role", Role.USER)
    if user_role not in [Role.ADMIN, Role.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin or Superadmin access required")
    return current_user

# Superadmin-only dependency
async def get_superadmin_user(current_user: dict = Depends(get_current_user)):
    user_role = current_user.user_metadata.get("role", Role.USER)
    if user_role != Role.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user

# Admin sign-up (requires superadmin privileges)
@router.post("/signup/admin")
async def signup_admin(user: UserSignup, current_user: dict = Depends(get_superadmin_user)):
    """
    Create a new admin user. Only superadmins can create admins.
    Only requires email and password.
    """
    try:
        supabase = get_supabase_admin_client()
        response = supabase.auth.admin.create_user({
            "email": user.email.lower(),
            "password": user.password,
            "user_metadata": {"role": Role.ADMIN},
            "email_confirm": True
        })
        
        if response.user:
            return {
                "message": "Admin created successfully", 
                "user_id": response.user.id,
                "role": Role.ADMIN
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create admin")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Admin-only: List all users
@router.get("/users")
async def list_users(current_user: dict = Depends(get_admin_user)):
    """
    Admin or Superadmin endpoint to list all users in the system.
    """
    try:
        supabase = get_supabase_admin_client()
        response = supabase.auth.admin.list_users()
        
        users = []
        for user in response:
            users.append({
                "id": user.id,
                "email": user.email,
                "role": user.user_metadata.get("role", Role.USER),
                "created_at": user.created_at,
                "email_confirmed": bool(user.email_confirmed_at),
                "last_sign_in": user.last_sign_in_at
            })
        
        return {"users": users, "count": len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin-only: Update user role
@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: Role, current_user: dict = Depends(get_admin_user)):
    """
    Admin or Superadmin endpoint to update a user's role.
    Superadmin required to set role to admin or superadmin.
    """
    try:
        if role in [Role.ADMIN, Role.SUPERADMIN]:
            user_role = current_user.user_metadata.get("role", Role.USER)
            if user_role != Role.SUPERADMIN:
                raise HTTPException(status_code=403, detail="Superadmin access required to set admin or superadmin role")
        
        supabase = get_supabase_admin_client()
        response = supabase.auth.admin.update_user_by_id(user_id, {
            "user_metadata": {"role": role.value}
        })
        
        return {
            "message": f"User role updated to {role.value}",
            "user_id": user_id,
            "new_role": role.value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Admin-only: Delete user
@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_admin_user)):
    """
    Admin or Superadmin endpoint to delete a user.
    Superadmin required to delete admin or superadmin users.
    """
    try:
        supabase = get_supabase_admin_client()
        target_user = supabase.auth.admin.get_user_by_id(user_id)
        target_role = target_user.user.user_metadata.get("role", Role.USER)
        
        if target_role in [Role.ADMIN, Role.SUPERADMIN]:
            current_user_role = current_user.user_metadata.get("role", Role.USER)
            if current_user_role != Role.SUPERADMIN:
                raise HTTPException(status_code=403, detail="Superadmin access required to delete admin or superadmin")
        
        supabase.auth.admin.delete_user(user_id)
        
        return {"message": "User deleted successfully", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Update email and/or password
@router.put("/users/{user_id}/update")
async def update_user(user_id: str, update_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    """
    Update a user's email and/or password.
    - Users can update their own email/password.
    - Admins can update users' email/password (not admins or superadmins).
    - Superadmins can update any user's email/password.
    """
    try:
        if not update_data.email and not update_data.password:
            raise HTTPException(status_code=400, detail="At least one of email or password must be provided")
        
        current_user_role = current_user.user_metadata.get("role", Role.USER)
        update_payload = {}
        if update_data.email:
            update_payload["email"] = update_data.email.lower()
        if update_data.password:
            update_payload["password"] = update_data.password
        
        # Case 1: User updating their own email/password
        if user_id == current_user.id:
            supabase = get_supabase_client()  # Assuming get_supabase_client is imported
            response = supabase.auth.update_user(update_payload)
            return {
                "message": "User updated successfully",
                "user_id": user_id,
                "updated_email": update_data.email if update_data.email else None,
                "password_updated": bool(update_data.password)
            }
        
        # Case 2: Admin or Superadmin updating another user
        supabase = get_supabase_admin_client()
        target_user = supabase.auth.admin.get_user_by_id(user_id)
        target_role = target_user.user.user_metadata.get("role", Role.USER)
        
        if current_user_role == Role.ADMIN and target_role in [Role.ADMIN, Role.SUPERADMIN]:
            raise HTTPException(status_code=403, detail="Admins cannot update other admins or superadmins")
        
        if current_user_role == Role.SUPERADMIN and update_data.email:
            update_payload["email_confirm"] = True
        
        response = supabase.auth.admin.update_user_by_id(user_id, update_payload)
        
        return {
            "message": "User updated successfully",
            "user_id": user_id,
            "updated_email": update_data.email if update_data.email else None,
            "password_updated": bool(update_data.password)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))