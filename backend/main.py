from fastapi import FastAPI

app = FastAPI(
    title="Task Tracker API",
    description="作業時間追跡とカテゴリ分類のためのAPI",
    version="0.1.0"
)

@app.get("/")
async def read_root():
    return {"message": "Task Tracker API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)