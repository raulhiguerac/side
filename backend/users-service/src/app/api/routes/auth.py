from fastapi import APIRouter

router = APIRouter(prefix="/register", tags=["auth"])

@router.post("/")
def register_user_generic_flow():