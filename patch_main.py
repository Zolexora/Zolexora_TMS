with open("backend/app/main.py", "r") as f:
    content = f.read()

content = content.replace(
    "from app.modules.auth.routes import router as auth_router",
    "from app.modules.auth.routes import router as auth_router\nfrom app.modules.extensions.r1rcm.routes import router as r1rcm_router"
)

content = content.replace(
    "app.include_router(auth_router)",
    "app.include_router(auth_router)\napp.include_router(r1rcm_router)"
)

with open("backend/app/main.py", "w") as f:
    f.write(content)
