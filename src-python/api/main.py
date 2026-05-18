from fastapi import FastAPI

app = FastAPI(title="CloudSaver Sidecar")


@app.get("/health")
async def health():
    return {"status": "ok"}
