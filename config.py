import os

osuclientid = os.getenv('OSU_CLIENT_ID')
osuclientsecret = os.getenv('OSU_CLIENT_SECRET')
remote_mongodb_uri = os.getenv('REMOTE_MONGO_URI')
local_mongodb_uri = os.getenv('LOCAL_MONGO_URI')

# 确保所有必要的配置都已设置
assert osuclientid, "OSU Client ID 未设置"
assert osuclientsecret, "OSU Client Secret 未设置"
assert remote_mongodb_uri, "Remote MongoDB URI 未设置"

print(f"Remote MongoDB URI: {remote_mongodb_uri}")
