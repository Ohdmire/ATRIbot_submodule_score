from fastapi import HTTPException
from pymongo import MongoClient
from config import remote_mongodb_uri,local_mongodb_uri
import logging

# 本地 MongoDB 配置
LOCAL_MONGO_URI = local_mongodb_uri
LOCAL_DB_NAME = "osu"
LOCAL_COLLECTION_UNRANKSCORE = "unrankscore"
LOCAL_COLLECTION_BIND = "bind"
LOCAL_COLLECTION_RANKSCORE = "score"
LOCAL_COLLECTION_USPUSH = "uspush"

# 远程 MongoDB 配置
REMOTE_MONGO_URI = remote_mongodb_uri
REMOTE_DB_NAME = "osu"
REMOTE_COLLECTION_BIND = "bind"
REMOTE_COLLECTION_UNRANKSCORE = "unrankscore"

# 初始化本地和远程 MongoDB 连接
local_client = MongoClient(LOCAL_MONGO_URI)
local_db = local_client[LOCAL_DB_NAME]
local_collection_unrankscore = local_db[LOCAL_COLLECTION_UNRANKSCORE]
local_collection_bind = local_db[LOCAL_COLLECTION_BIND]
local_collection_rankscore = local_db[LOCAL_COLLECTION_RANKSCORE]
local_collection_uspush = local_db[LOCAL_COLLECTION_USPUSH]

remote_client = MongoClient(REMOTE_MONGO_URI)
remote_db = remote_client[REMOTE_DB_NAME]
remote_collection_bind = remote_db[REMOTE_COLLECTION_BIND]
remote_collection_unrankscore= remote_db[REMOTE_COLLECTION_UNRANKSCORE]


def sync_remote_bind_to_local():
    try:
        # 从远程 MongoDB 获取所有 bind 文档
        remote_bind_docs = remote_collection_bind.find()

        # 遍历远程文档
        for doc in remote_bind_docs:
            doc.pop('_id', None) # 清除可能冲突的字段

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

def pull_remote_unrankscore_to_local():

    count_unrankscore_pulled = 0
    try:

        # 批量获取所有远程ID
        remote_ids = list(remote_collection_unrankscore.distinct("id"))
        
        # 返回不在本地 在远程的score id
        to_insert_ids = list(local_collection_unrankscore.distinct(
            "id", {"id": {"$nin": remote_ids}}
        ))
        logging.info(f'to insert ids{to_insert_ids}')
        for i in to_insert_ids:
            new_doc = remote_collection_unrankscore.find_one({"id": i})
            if new_doc is None:
                logging.error(f'error id{i}')
            new_doc.pop('_id', None) # 清除可能冲突的字段
            local_collection_unrankscore.update_one({"id":new_doc["id"]},{"$set": new_doc},upsert=True)
            count_unrankscore_pulled +=1

        return {"status": "success", "message": "Pull remote successfully.","data":count_unrankscore_pulled}
    
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

def push_uspush_to_remote():

    count_unrankscore_pushed = 0

    try:

        # 批量获取远程ID
        remote_ids = list(remote_collection_unrankscore.distinct("id"))

        # 返回不在远程的所有来自local_uspush的score id
        to_push_ids = list(local_collection_uspush.distinct(
            "id", {"id": {"$nin": remote_ids}}
        ))
        logging.info(f'to push ids{to_push_ids}')
        for i in to_push_ids:
            new_doc = local_collection_uspush.find_one({"id": i})
            new_doc.pop('_id', None) # 清除可能冲突的字段
            remote_collection_unrankscore.update_one({"id":new_doc["id"]},{"$set": new_doc},upsert=True)
            count_unrankscore_pushed +=1

        # 最后没有任何问题drop掉待push的表
        local_collection_uspush.delete_many({})

        return {"status": "success", "message": "Sync to Remote completed successfully.","data":count_unrankscore_pushed}

    except Exception as e:
        logging.error(e)
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

def write_score_to_us_push_db(data):
    local_collection_uspush.update_one({"id":data["id"]},{"$set": data},upsert=True)

def write_score_to_db(datas):

    for data in datas:
        if data["beatmap"]["ranked"] == 1 or data["beatmap"]["ranked"] == 2 or data["beatmap"]["ranked"] == 4:
            write_to_ranked_socre(data)
        else:
            write_to_unranked_score(data)
            write_score_to_us_push_db(data)





