import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from information_retrieval.vector_space_model import build_vector_space_model, execute_singualar_value_decomposition
from information_retrieval.boolean_model import build_boolean_model
from preprocessing.preprocessing import preprocess_documents
from api.vector_space_api import router as vector_space_router
from api.boolean_api import router as boolean_router
from db.helper import init_database
from db.session import init_db_schema
from information_retrieval.globals import init_globals
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
import uvicorn

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI app started.")

    await init_db_schema()
    await init_database()

    init_globals()
    await preprocess_documents()
    await build_boolean_model()
    await build_vector_space_model()
    await execute_singualar_value_decomposition()

    yield


app = FastAPI(
    title="Information Retrieval API",
    description="API for Information Retrieval System.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(vector_space_router, tags=["Vector Space Search"])
app.include_router(boolean_router, tags=["Boolean Search"])

# Enable CORS for the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
