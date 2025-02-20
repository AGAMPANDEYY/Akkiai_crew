import hmac 
import hashlib
import os 

message="Since i was a child i had an interest in surfing"
entity_id="agampandey"
upsert_type="perm_kb"

secret_key=os.getenv("SECRET_KEY")

data=f"{message}|{entity_id}|{upsert_type}"
print(data)

hash=hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

print(hash)