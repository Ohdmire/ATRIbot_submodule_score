from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
import uvicorn
from api import refresh_token,job_get_pr_info
from table import get_all_users_id
from table import sync_remote_bind_to_local

scheduler = AsyncIOScheduler()

async def check_url_status(url: str):
    try:
        async with aiohttp.ClientSession as session:
            response = await session.get(url)
            return response.status == 200
    except Exception as e:
        print(f"Error checking URL: {e}")
        return False

def on_failure_action():
    print("URL check failed! Taking action...")

async def scheduled_task(url: str):
    if not await check_url_status(url):
        on_failure_action()

def job_refresh_token():
    refresh_token()


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # 添加定时任务，每60秒执行一次
    scheduler.add_job(refresh_token, 'interval', seconds=3600)
    scheduler.add_job(fetch_all_user_scores, 'cron', hour='8,16,0')
    scheduler.add_job(sync, 'cron', hour='7,15,23')
    scheduler.start()
    yield
    # 关闭调度器
    scheduler.shutdown()

app = FastAPI(lifespan=app_lifespan)

@app.get("/")
async def read_root():
    return {"message": "FastAPI定时器运行中"}

@app.get("/trigger")
@app.post("/trigger")
async def fetch_all_user_scores():
    users_list = get_all_users_id()
    await job_get_pr_info(users_list)
    return 'finished'

@app.get("/sync")
@app.post("/sync")
async def sync():
    result = sync_remote_bind_to_local()
    return result

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8009, reload=True, timeout_keep_alive=120)
