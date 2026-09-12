import re

with open("apps/tms-api/app/modules/billing/routes.py", "r") as f:
    content = f.read()

imports = """
from app.modules.billing.models import RateCard, RateCardVersion, RateCardRule, RateCardSide
from app.modules.billing.schemas import RateCardCreate, RateCardResponse, RateCardVersionCreate
"""

# Insert imports after router = APIRouter()
content = content.replace("router = APIRouter()", "router = APIRouter()\n" + imports)

crud_routes = """
@router.post("/rate-cards", response_model=RateCardResponse)
async def create_rate_card(
    payload: RateCardCreate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rate_card = RateCard(
        organisation_id=current_user.organisation_id,
        name=payload.name,
        description=payload.description,
        side=RateCardSide(payload.side),
        customer_id=payload.customer_id,
        vendor_id=payload.vendor_id,
        service_type=payload.service_type,
        vehicle_category_id=payload.vehicle_category_id,
        currency=payload.currency,
        active=payload.active
    )
    
    if payload.initial_version:
        version = RateCardVersion(
            version_number=payload.initial_version.version_number,
            effective_from=payload.initial_version.effective_from,
            effective_to=payload.initial_version.effective_to,
            is_immutable=payload.initial_version.is_immutable
        )
        for rule_data in payload.initial_version.rules:
            rule = RateCardRule(**rule_data.model_dump())
            version.rules.append(rule)
        rate_card.versions.append(version)
        
    db.add(rate_card)
    await db.commit()
    await db.refresh(rate_card)
    return rate_card

@router.get("/rate-cards", response_model=List[RateCardResponse])
async def list_rate_cards(
    side: str | None = None,
    customer_id: uuid.UUID | None = None,
    vendor_id: uuid.UUID | None = None,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(RateCard).filter(RateCard.organisation_id == current_user.organisation_id).options(selectinload(RateCard.versions).selectinload(RateCardVersion.rules))
    if side:
        query = query.filter(RateCard.side == RateCardSide(side))
    if customer_id:
        query = query.filter(RateCard.customer_id == customer_id)
    if vendor_id:
        query = query.filter(RateCard.vendor_id == vendor_id)
        
    result = await db.execute(query)
    return result.scalars().all()
"""

# Append CRUD routes at the end
with open("apps/tms-api/app/modules/billing/routes.py", "w") as f:
    f.write(content + "\n" + crud_routes)
