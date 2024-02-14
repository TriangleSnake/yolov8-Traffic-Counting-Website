import uuid

token = str(uuid.uuid4())

print(token)

with open('token.txt','a') as f:
    f.write(token+'\n')