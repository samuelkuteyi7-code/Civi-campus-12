from fastapi.responses import FileResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from App.database.db import Base, engine
from App.routes import auth
from App.routes import sug
from App.routes import promise
from App.routes import report
from App.routes import media
from App.routes import article
from App.routes import chat

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CiviAI Campus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sug.router)
app.include_router(promise.router)
app.include_router(report.router)
app.include_router(media.router)
app.include_router(article.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return FileResponse("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
