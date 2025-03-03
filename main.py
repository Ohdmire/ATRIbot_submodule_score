from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
import uvicorn
from api import refresh_token,job_get_pr_info
from table import get_all_users_id
from table import sync_remote_bind_to_local
import logging

scheduler = AsyncIOScheduler()

# 设置日志级别和格式
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
    logging.info("亚托莉子模块，启动")
    # 添加定时任务，每60秒执行一次
    scheduler.add_job(refresh_token, 'interval', seconds=3600)
    scheduler.add_job(fetch_all_user_scores, 'cron', hour='8,16,0')
    scheduler.add_job(sync, 'cron', hour='7,15,23')
    scheduler.start()
    yield
    # 关闭调度器
    scheduler.shutdown()
    logging.info("亚托莉子模块，关闭")

app = FastAPI(lifespan=app_lifespan)

@app.api_route("/trigger", methods=["GET", "POST"])
async def fetch_all_user_scores():
    users_list = get_all_users_id()
    await job_get_pr_info(users_list)
    logging.info("已执行抓取操作")
    return 'finished'

@app.api_route("/sync", methods=["GET", "POST"])
async def sync():
    result = sync_remote_bind_to_local()
    logging.info("已同步bind表")
    return result

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8009, reload=True, timeout_keep_alive=120)
