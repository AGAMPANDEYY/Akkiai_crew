import hmac 
import hashlib
import os 

MESSAGE="Since i was a child i had an interest in surfing"
ENTITY_ID="agampandey"
UPSERT_TYPE="perm_kb"

secret_key=os.getenv("SECRET_KEY")

data=f"{MESSAGE}|{ENTITY_ID}|{UPSERT_TYPE}"

hash=hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

print(hash)