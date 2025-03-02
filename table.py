from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from config import remote_mongodb_uri,local_mongodb_uri

app = FastAPI()

# 本地 MongoDB 配置
LOCAL_MONGO_URI = local_mongodb_uri
LOCAL_DB_NAME = "osu"
LOCAL_COLLECTION_UNRANKSCORE = "unrankscore"
LOCAL_COLLECTION_BIND = "bind"
LOCAL_COLLECTION_RANKSCORE = "score"

# 远程 MongoDB 配置
REMOTE_MONGO_URI = remote_mongodb_uri
REMOTE_DB_NAME = "osu"
REMOTE_COLLECTION_BIND = "bind"

# 初始化本地和远程 MongoDB 连接
local_client = MongoClient(LOCAL_MONGO_URI)
local_db = local_client[LOCAL_DB_NAME]
local_collection_unrankscore = local_db[LOCAL_COLLECTION_UNRANKSCORE]
local_collection_bind = local_db[LOCAL_COLLECTION_BIND]
local_collection_rankscore = local_db[LOCAL_COLLECTION_RANKSCORE]

remote_client = MongoClient(REMOTE_MONGO_URI)
remote_db = remote_client[REMOTE_DB_NAME]
remote_collection_bind = remote_db[REMOTE_COLLECTION_BIND]


def sync_remote_bind_to_local():
    try:
        # 从远程 MongoDB 获取所有 bind 文档
        remote_bind_docs = remote_collection_bind.find()

        # 遍历远程文档
        for doc in remote_bind_docs:

            # 检查本地是否存在相同 id 的文档
            local_doc = local_collection_bind.find_one({"id": doc["id"]})

            if local_doc:
                # 如果存在，更新本地文档
                local_collection_bind.update_one({"id": doc["id"]}, {"$set": doc})
            else:
                # 如果不存在，插入新文档
                local_collection_bind.insert_one(doc)

        return {"status": "success", "message": "Sync completed successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


def get_all_users_id() -> list:

    users_list = []

    users = local_collection_bind.find()

    for user in users:

        users_list.append(user["user_id"])

    return users_list

def write_to_ranked_socre(data):
    local_collection_rankscore.update_one({"id":data["id"]},{"$set": data},upsert=True)

def write_to_unranked_score(data):
    local_collection_unrankscore.update_one({"id":data["id"]},{"$set": data},upsert=True)

def write_score_to_db(datas):

    for data in datas:
        if data["beatmap"]["ranked"] == 1 or data["beatmap"]["ranked"] == 2 or data["beatmap"]["ranked"] == 4:
            write_to_ranked_socre(data)
        else:
            write_to_unranked_score(data)



