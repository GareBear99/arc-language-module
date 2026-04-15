from __future__ import annotations
from fastapi import FastAPI
from arc_lang.api.routes import router

app = FastAPI(title="ARC Language Module", version="0.24.0")
app.include_router(router)
