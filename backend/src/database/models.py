from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

# 基础类
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")
    liked_combinations = relationship("LikedCombination", back_populates="user", cascade="all, delete-orphan")

class Preference(Base):
    __tablename__ = "preferences"
    id = Column(Integer, primary_key=True, index=True)
    ingredient_name = Column(String, index=True)
    liked = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="preferences")

class LikedCombination(Base):
    __tablename__ = "liked_combinations"
    id = Column(Integer, primary_key=True, index=True)
    signature = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="liked_combinations")
    ingredients = relationship("CombinationIngredient", back_populates="combination", cascade="all, delete-orphan")

class CombinationIngredient(Base):
    __tablename__ = "combination_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    ingredient_name = Column(String, index=True)
    combination_id = Column(Integer, ForeignKey("liked_combinations.id"))
    
    combination = relationship("LikedCombination", back_populates="ingredients")