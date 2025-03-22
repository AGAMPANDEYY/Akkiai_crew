import hmac
import hashlib
import os 

solution_id="5"
input1="Akki AI is a Multi-Agent AI CoPilot for Founders and Investors.\n\nThis helps founders to get quick and accurate feedback on different aspects of their startup pitch, strategy, and operations. On the other hand, it helps investor analysts evaluate and analyze thousands of idea pitches/applications, identifying potential unicorns, saving them time and cost."
input2="string"
input3="string"
input4="string"
input5="string"
input6="string"
input7="string"

secret_key=os.getenv("SECRET_KEY")
#data=f"{solution_id}|{input1}|{input2}|{input3}"
data=f"{solution_id}|{input1}"

hash=hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

print(hash)