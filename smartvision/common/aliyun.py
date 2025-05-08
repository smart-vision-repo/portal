import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

BUCKET_NAME = "smart-vision"

end_point = os.getenv("ALIYUN_OSS_END_POINT")
oss_access_key = os.getenv("ALIYUN_OSS_ASSESS_KEY")
oss_access_key_secret = os.getenv("ALIYUN_OSS_SECRET_KEY")

auth = oss2.Auth(oss_access_key, oss_access_key_secret)
bucket = oss2.Bucket(auth, end_point, BUCKET_NAME)
headers = {"Content-Type": "image/jpeg", "Content-Disposition": "inline"}  # 对于JPG图片

def aliyu_oss_put_object(local_file, object_name):
    with open(local_file, "rb") as f:
        bucket.put_object(object_name, f, headers=headers)

def put_identified_objects(transaction_id: str, images: list):
    if not images:
        return
    
    for image in images:
        print(f">>>>>>>>{image}")
        file_name = image.split("/")[-1]
        aliyu_oss_put_object(image, f"identified/{transaction_id}/{file_name}")

if __name__ == "__main__":
    file = "/var/tmp/smart-vision/image/02937de2-6bc3-474a-9ca5-fa0b418a2755/01-00-00-00-01-00001.jpg"
    put_identified_objects("hello",  [file])
