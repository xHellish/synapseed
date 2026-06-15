# Capa de repositorios — exports centralizados.
#
# Uso en un endpoint:
#   from app.repositories import UserRepository, ProductRepository
#   from app.db.session import get_db
#
#   @router.get("/")
#   async def list_users(db: AsyncSession = Depends(get_db)):
#       repo = UserRepository(db)
#       return await repo.get_all_active()

from app.repositories.audit_repository import AuditRepository
from app.repositories.base import BaseRepository
from app.repositories.distributor_repository import DistributorRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.zone_repository import ZoneRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ProductRepository",
    "ZoneRepository",
    "RecommendationRepository",
    "DistributorRepository",
    "AuditRepository",
]
