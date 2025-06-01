# gateway/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001/auth")
WATCHLIST_SERVICE_URL = os.getenv("WATCHLIST_SERVICE_URL", "http://localhost:8001/watchlist")
PORTFOLIO_SERVICE_URL = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8001/portfolio")
STOCK_SERVICE_URL = os.getenv("STOCK_SERVICE_URL", "http://localhost:8002/stocks")
NEWS_SERVICE_URL = os.getenv("NEWS_SERVICE_URL", "http://localhost:8002/news")
LLM_SERVICE_URL=  os.getenv("LLM_SERVICE_URL", "http://localhost:8002/chat-gpt")
COMPANY_SERVICE_URL=  os.getenv("COMPANY_SERVICE_URL", "http://localhost:8002/companies")
FINANCIAL_SERVICE_URL=  os.getenv("FINANCIAL_SERVICE_URL", "http://localhost:8002/financial")
LSTM_SERVICE_URL=  os.getenv("LSTM_SERVICE_URL", "http://localhost:8002/forecast")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)
    return response

from fastapi import Response

@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user(path: str, request: Request):
    url = f"{AUTH_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@app.api_route("/api/watchlist/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user(path: str, request: Request):
    url = f"{WATCHLIST_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
@app.api_route("/api/chat-gpt/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user(path: str, request: Request):
    url = f"{LLM_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@app.api_route("/api/companies/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user(path: str, request: Request):
    url = f"{COMPANY_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.api_route("/api/portfolio/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user(path: str, request: Request):
    url = f"{PORTFOLIO_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@app.api_route("/api/stocks/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user(path: str, request: Request):
    url = f"{STOCK_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
@app.api_route("/api/news/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user(path: str, request: Request):
    url = f"{NEWS_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.api_route("/api/financial/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_user(path: str, request: Request):
    url = f"{FINANCIAL_SERVICE_URL}/{path}"
    print(url)
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

@app.api_route("/api/forecast/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_lstm(path: str, request: Request):
    url = f"{LSTM_SERVICE_URL}/{path}"
    print(url)
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
