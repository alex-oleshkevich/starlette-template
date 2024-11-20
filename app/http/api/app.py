from fastapi import FastAPI

from app.config import settings

api_app = FastAPI(debug=settings.debug)
