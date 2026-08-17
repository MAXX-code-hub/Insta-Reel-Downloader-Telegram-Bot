from fastapi import FastAPI, Query
from urllib.parse import urlparse

app = FastAPI()


@app.get("/")
def home():
    return {"message": "My API is working!"}


@app.get("/download")
def download(url: str = Query(...)):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return {
            "status": "error",
            "message": "Invalid URL"
        }

    if "instagram.com" in parsed.netloc.lower():
        return {
            "status": "success",
            "platform": "instagram",
            "content_type": "reel" if "/reel/" in parsed.path else "post",
            "url": url,
            "media_url": None,
            "message": "Instagram URL received. Media source not available yet."
        }

    return {
        "status": "success",
        "platform": "unknown",
        "content_type": "url",
        "url": url,
        "media_url": None
    }