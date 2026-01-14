"""
Repositorio para operaciones de autenticación.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

# TODO: Descomentar cuando el modelo User esté implementado
# from db.models import User


class AuthRepository:
    """Repositorio para gestionar operaciones de autenticación."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str):  # -> Optional[User]:
        """Obtiene usuario por email."""
        # TODO: Descomentar cuando User esté implementado
        # result = await self.db.execute(
        #     select(User).where(User.email == email, User.is_active == True)
        # )
        # return result.scalar_one_or_none()
        pass
    
    async def get_user_by_id(self, user_id: UUID):  # -> Optional[User]:
        """Obtiene usuario por ID."""
        # TODO: Descomentar cuando User esté implementado
        # result = await self.db.execute(
        #     select(User).where(User.id == user_id, User.is_active == True)
        # )
        # return result.scalar_one_or_none()
        pass
    
    async def create_user(self, email: str, hashed_password: str, **kwargs):  # -> User:
        """
        Crea un nuevo usuario.
        
        Args:
            email: Email del usuario
            hashed_password: Contraseña hasheada
            **kwargs: Campos adicionales del usuario
            
        Returns:
            Usuario creado
        """
        # TODO: Descomentar cuando User esté implementado
        # user = User(
        #     email=email,
        #     hashed_password=hashed_password,
        #     **kwargs
        # )
        # self.db.add(user)
        # await self.db.commit()
        # await self.db.refresh(user)
        # return user
        pass
    
    async def update_user_last_login(self, user_id: UUID) -> None:
        """
        Actualiza la última fecha de login del usuario.
        
        Args:
            user_id: ID del usuario
        """
        # TODO: Descomentar cuando User esté implementado
        # from datetime import datetime
        # user = await self.get_user_by_id(user_id)
        # if user:
        #     user.last_login = datetime.utcnow()
        #     await self.db.commit()
        pass
    
    async def verify_user_is_active(self, user_id: UUID) -> bool:
        """
        Verifica si un usuario está activo.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si está activo, False si no
        """
        # TODO: Descomentar cuando User esté implementado
        # user = await self.get_user_by_id(user_id)
        # return user.is_active if user else False
        return True
