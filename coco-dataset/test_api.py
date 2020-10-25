
from init import ERR_LOGGER
import requests
import os
import json
def object_api(file_name):


    with open(file_name, 'rb') as f:
        read_data = f.read()
    files = {
        'file': read_data,
    }
    response = requests.post('http://api:5000/upload/', files=files)
    data = response.content.decode()
    data = json.loads(data)
    print(data)
    return data

def predict(file_name):
    try:
        objects = object_api(file_name)
        # objects = ' '.join(objects)
        print("this is obj",objects)
        os.remove(file_name)
        return objects
    except Exception as e:
        print(str(e)+"Exception in predict")
        ERR_LOGGER(str(e)+" Exception in predict")
        return ""


import requests
import json
with open('test_image/sehore.jpg', 'rb') as f:
    read_data = f.read()

files = {
    'file': read_data,
}

response = requests.post('http://api:5000/upload/', files=files)
data = response.content.decode()
data = json.loads(data)
print(data, type(data))
