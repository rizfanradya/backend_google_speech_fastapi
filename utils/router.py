from fastapi import APIRouter
import api.user as user
import api.auth as auth
import api.role as role
import api.app as app
import api.google_speech as google_speech

routers = [
    (auth.router, "Auth API", "/api"),
    (role.router, "Role API", "/api/role"),
    (user.router, "User API", "/api/user"),
    (app.router, "App API", "/api/app"),
    (google_speech.router, "Google Speech API", "/api/speech"),
]

sorted_routers = sorted(routers, key=lambda x: x[1])
router = APIRouter()
for router_instance, tag, prefix in sorted_routers:
    router.include_router(router_instance, tags=[tag], prefix=prefix)
