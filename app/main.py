from fastapi import FastAPI

app = FastAPI(
    title="Research Blog & Project Discussion Board"
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}