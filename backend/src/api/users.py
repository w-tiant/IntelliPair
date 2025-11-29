
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel

from ..core.dependencies import get_db, get_app_data
from ..database.models import User, Preference, LikedCombination, CombinationIngredient
from ..schemas.main_schemas import CombinationPayload
from ..services import helpers

router = APIRouter(
    prefix="/api/users",
    tags=["User Management"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/login")
def login_or_register(user_data: UserLogin, db: Session = Depends(get_db)):
    username = user_data.username
    password = user_data.password
    
    if not username or not password:
         raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    db_user = db.query(User).filter(User.username == username).first()
    
    if db_user:
        if not verify_password(password, db_user.hashed_password):
             raise HTTPException(status_code=400, detail="密码错误")
        return {"id": db_user.id, "username": db_user.username, "message": "登录成功"}
    
    else:
        hashed_password = get_password_hash(password)
        new_user = User(username=username, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.id, "username": new_user.username, "message": "注册并登录成功"}

@router.post("/{username}/preferences")
def toggle_preference(
    username: str,
    ingredient: str = Query(...),
    db: Session = Depends(get_db),
    app_data: dict = Depends(get_app_data)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        _, canonical_name = helpers.get_vector_by_name(ingredient, app_data)
    except HTTPException as e:
        raise e

    existing_pref = db.query(Preference).filter(
        Preference.user_id == user.id,
        Preference.ingredient_name == canonical_name
    ).first()

    if existing_pref:
        db.delete(existing_pref)
        db.commit()
        return {"status": "success", "action": "unliked", "ingredient": canonical_name}
    else:
        new_pref = Preference(ingredient_name=canonical_name, user_id=user.id)
        db.add(new_pref)
        db.commit()
        return {"status": "success", "action": "liked", "ingredient": canonical_name}


@router.post("/{username}/combinations/toggle")
def toggle_combination_preference(
    username: str,
    payload: CombinationPayload,
    db: Session = Depends(get_db),
    app_data: dict = Depends(get_app_data) # <--- 注入 app_data
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    canonical_names = []
    for ingr in payload.combination:
        try:
            _, canonical = helpers.get_vector_by_name(ingr, app_data)
            canonical_names.append(canonical)
        except HTTPException:
            continue

    if not canonical_names:
        raise HTTPException(status_code=400, detail="组合中没有有效的食材。")

    canonical_names.sort()
    signature = ",".join(canonical_names)

    existing_combo = db.query(LikedCombination).filter(
        LikedCombination.user_id == user.id,
        LikedCombination.signature == signature
    ).first()

    if existing_combo:
        db.delete(existing_combo)
        db.commit()
        return {"status": "success", "action": "unliked", "signature": signature}
    else:
        new_combo = LikedCombination(signature=signature, user_id=user.id)
        for name in canonical_names:
            new_combo.ingredients.append(CombinationIngredient(ingredient_name=name))
        db.add(new_combo)
        db.commit()
        return {"status": "success", "action": "liked", "signature": signature}