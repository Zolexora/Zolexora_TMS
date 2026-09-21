import uuid
from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tenant import TenantContext

T = TypeVar("T")

class BaseTenantRepository(Generic[T]):
    """
    Base repository enforcing strict tenant isolation for all database operations.
    Prevents cross-tenant data leakage by automatically appending organisation_id filters.
    """
    def __init__(self, model: Type[T], db: AsyncSession, tenant: TenantContext):
        self.model = model
        self.db = db
        self.tenant = tenant
        
        # Verify the model actually has an organisation_id column to prevent accidental global exposure
        if not hasattr(model, "organisation_id"):
            raise ValueError(f"Model {model.__name__} is not tenant-aware (missing organisation_id). Cannot use BaseTenantRepository.")

    def _tenant_filter(self):
        return self.model.organisation_id == self.tenant.organisation_id

    async def get_by_id(self, id: uuid.UUID) -> Optional[T]:
        stmt = select(self.model).where(self.model.id == id, self._tenant_filter())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        stmt = select(self.model).where(self._tenant_filter()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        # Enforce the tenant ID automatically. Overrides any malicious input.
        kwargs["organisation_id"] = self.tenant.organisation_id
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def update(self, id: uuid.UUID, **kwargs) -> Optional[T]:
        # Strip organisation_id from kwargs so a malicious user can't transfer ownership
        kwargs.pop("organisation_id", None)
        
        stmt = (
            update(self.model)
            .where(self.model.id == id, self._tenant_filter())
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        updated_instance = result.scalars().first()
        if updated_instance:
            await self.db.flush()
        return updated_instance

    async def delete(self, id: uuid.UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == id, self._tenant_filter())
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0
