import asyncio
from httpx import ASGITransport, AsyncClient
import uuid
from apps.tms_api.tests.api.test_phase7_core import make_test_token, app

async def run():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        user_a = uuid.uuid4()
        token_a = make_test_token(user_a, "user_a_lifecycle@tenant-a.com")
        res_a = await client.post(
            "/api/v1/onboarding",
            json={"name": f"Lifecycle Tenant {uuid.uuid4().hex[:6]}", "organisation_type": "Private Limited Company"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        print("STATUS:", res_a.status_code)
        print("BODY:", res_a.text)

if __name__ == "__main__":
    asyncio.run(run())
