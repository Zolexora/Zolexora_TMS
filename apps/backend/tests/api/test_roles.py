import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.main import app
import uuid
from jose import jwt
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.modules.identity.organisations.models import Organisation, OrganisationStatus, OrganisationType
from app.modules.identity.organisations.membership_models import OrganisationMember, MemberStatus

def make_test_token(user_id: uuid.UUID, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "exp": 9999999999,
    }
    return jwt.encode(payload, settings.JWT_SECRET or "test-jwt-secret-for-testing", algorithm="HS256")

@pytest.fixture(autouse=True)
def mock_audit(monkeypatch):
    from app.modules.identity.roles import service
    async def _mock_audit(*args, **kwargs):
        pass
    monkeypatch.setattr(service, "_audit", _mock_mock_audit := _mock_audit)


@pytest.mark.asyncio
async def test_roles_flow(monkeypatch):
    """
    Integration test covering Prompt 07 role requirements:
    - Platform templates available
    - Commander has all effective permissions
    - Create a role
    - Assign role to member
    - Member gets role permissions
    - Add overrides
    - Member permissions update accordingly
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # 1. Direct DB Setup for Commander and Org
        user1_id = uuid.uuid4()
        org_id = uuid.uuid4()
        
        async with AsyncSessionLocal() as db:
            await db.execute(text("""
                INSERT INTO organisations (id, name, organisation_type, status, created_at, updated_at)
                VALUES (:oid, :name, :type, 'ACTIVE', now(), now())
            """), {"oid": org_id, "name": "Roles Test Org", "type": "Private Limited Company"})
            
            await db.execute(text("""
                INSERT INTO organisation_members (id, organisation_id, user_id, status, is_creator, is_commander, created_at, updated_at)
                VALUES (:mid, :oid, :uid, 'ACTIVE', true, true, now(), now())
            """), {"mid": uuid.uuid4(), "oid": org_id, "uid": user1_id})
            
            await db.commit()

        token1 = make_test_token(user1_id, "commander@example.com")

        # 2. Check Platform Templates exist
        tpl_res = await client.get(
            "/api/v1/platform-role-templates",
            headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org_id)}
        )
        assert tpl_res.status_code == 200
        assert len(tpl_res.json()) >= 5

        # 3. Verify Commander Effective Permissions
        eff_res_cdr = await client.get(
            "/api/v1/organisations/me/effective-permissions",
            headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org_id)}
        )
        assert eff_res_cdr.status_code == 200
        cdr_perms = eff_res_cdr.json()
        assert cdr_perms["is_commander"] is True
        assert len(cdr_perms["permissions"]) > 10 # Commander gets all caps

        # 4. Invite a member (using direct DB to bypass email)
        user2_id = uuid.uuid4()
        member2_id = uuid.uuid4()
        async with AsyncSessionLocal() as db:
            member2 = OrganisationMember(
                id=member2_id,
                organisation_id=org_id,
                user_id=user2_id,
                status=MemberStatus.ACTIVE,
                is_creator=False,
                is_commander=False
            )
            db.add(member2)
            await db.commit()

        token2 = make_test_token(user2_id, "member@example.com")

        # 5. Commander creates a role
        role_res = await client.post(
            "/api/v1/organisations/roles",
            json={
                "name": "Dispatcher Plus",
                "permissions": [
                    {"module_code": "operations", "page_code": "bookings", "action_code": "view"},
                    {"module_code": "operations", "page_code": "dispatch", "action_code": "view"}
                ]
            },
            headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org_id)}
        )
        assert role_res.status_code == 201
        role_id = role_res.json()["id"]

        # 6. Assign role
        assign_res = await client.put(
            f"/api/v1/organisations/members/{member2_id}/role",
            json={"role_id": role_id},
            headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org_id)}
        )
        assert assign_res.status_code == 200

        # 7. Check member permissions
        eff_res_mem = await client.get(
            "/api/v1/organisations/me/effective-permissions",
            headers={"Authorization": f"Bearer {token2}", "X-Organization-Id": str(org_id)}
        )
        assert eff_res_mem.status_code == 200
        mem_perms = eff_res_mem.json()
        assert mem_perms["is_commander"] is False
        assert "operations.bookings.view" in mem_perms["permissions"]
        assert "fleet.vehicles.view" not in mem_perms["permissions"]

        # 8. Add Overrides (Grant Fleet, Restrict Dispatch)
        await client.post(
            f"/api/v1/organisations/members/{member2_id}/permission-overrides",
            json={
                "override_type": "GRANT",
                "module_code": "fleet",
                "page_code": "vehicles",
                "action_code": "view"
            },
            headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org_id)}
        )
        await client.post(
            f"/api/v1/organisations/members/{member2_id}/permission-overrides",
            json={
                "override_type": "RESTRICT",
                "module_code": "operations",
                "page_code": "dispatch",
                "action_code": "view"
            },
            headers={"Authorization": f"Bearer {token1}", "X-Organization-Id": str(org_id)}
        )

        # 9. Verify updated effective permissions
        eff_res_mem_updated = await client.get(
            "/api/v1/organisations/me/effective-permissions",
            headers={"Authorization": f"Bearer {token2}", "X-Organization-Id": str(org_id)}
        )
        updated_perms = eff_res_mem_updated.json()["permissions"]
        assert "operations.bookings.view" in updated_perms # from role
        assert "fleet.vehicles.view" in updated_perms # from grant
        assert "operations.dispatch.view" not in updated_perms # restricted
