import uvicorn

if __name__ == "__main__":
    # Start the FastAPI application server
    uvicorn.run("app.main:app", host="127.0.0.1", port=5000, reload=True)
