from config import osuclientid, osuclientsecret
import aiohttp
import asyncio
import requests
from table import write_score_to_db

client_id = osuclientid
client_secret = osuclientsecret

# 获取访问令牌
token = None

# 定义headers
headers = {'Authorization': f'Bearer {token}', 'x-api-version': '20240529'}

def refresh_token():
    global token, headers
    url = 'https://osu.ppy.sh/oauth/token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'public'
    }
    response = requests.post(url, data=data)
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'x-api-version': '20240529'}

refresh_token()

async def get_user_passrecent_info(user_id, session):
    url = f'https://osu.ppy.sh/api/v2/users/{user_id}/scores/recent?legacy_only=0&include_fails=0&mode=osu&limit=100'
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 429:  # 遇到429错误
                raise Exception("Rate limit exceeded")
            data = await response.json()
            return data
    except Exception as e:
        print(f"Request failed for user {user_id}: {e}")
        raise  # 抛出异常以便稍后重试


async def worker(queue, session):
    while True:
        user_id = await queue.get()
        try:
            datas = await get_user_passrecent_info(user_id, session)
            write_score_to_db(datas)  # 调用写入数据库的函数
        except Exception as e:
            if "Rate limit exceeded" in str(e):  # 只有429错误才重试
                await queue.put(user_id)  # 重新加入队列
            else:
                print(f"Skipping user {user_id} due to error: {e}")
        finally:
            queue.task_done()

async def job_get_pr_info(userlist):
    queue = asyncio.Queue()

    # 将所有用户ID加入队列
    for user_id in userlist:
        await queue.put(user_id)

    async with aiohttp.ClientSession() as session:
        # 创建4个worker协程
        workers = [asyncio.create_task(worker(queue, session)) for _ in range(4)]
        await queue.join()  # 等待队列中的所有任务完成

        # 取消worker协程
        for w in workers:
            w.cancel()
