#AI Contribution Weight: [100%] AI Generated / [0%] Human Refactored

from fastapi import FastAPI

app = FastAPI(
    title="Research Blog & Project Discussion Board"
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}