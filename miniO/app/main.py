from contextlib import asynccontextmanager
from fastapi import FastAPI


from app.database import engine
from app.models import Base
from app.dependencies import get_storage
from app.router import router



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    storage = get_storage()
    await storage.ensure_bucket()

    print("App ready")

    yield
    await engine.dispose()
    print("App stopped")


app = FastAPI(title="Note Taking API", lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}

