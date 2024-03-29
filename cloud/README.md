# Cloud

It is a cloud service for file upload/download and pin message.

## How to use it

### 0. Prerequisite

add Firebase Admin SDK
```
pip3 install firebase-admin
```

### 1. Generate private key

Replace serviceAccountKey.json with your key</br>
https://firebase.google.com/docs/admin/setup#initialize-sdk

###
### For Cloud module:
### 2. Update the config

Enable Cloud module and fill in the bucket name

config.ini:
```
cloud_module = on
fb_bucket_name = YOUR_BUCKET_NAME
```

### 3. Create a collection named "pin" in Firestore Database

###
### For FxStock module deployed to AWS:
### 2. Update the config

Enable FxStock module & cloud database, and fill in the bucket name

config.ini:
```
fxstock_module = on
cloud_db = on
fb_bucket_name = YOUR_BUCKET_NAME
```

### 3. Create a collection named "alert" in Firestore Database

### Note:
1. "Send Media" and "Send Stickers & GIFs" permissions have to be enabled in group
2. sending by URL in sendDocument will currently only work for gif, pdf and zip files
3. bots can download files of up to 20MB in size for the moment
4. if running on AWS Lambda, you may encounter firebase_admin module import issue<br/>
https://simonlaw-9918.medium.com/troubleshooting-export-platform-specific-python-package-using-docker-f4f41685924b
<br/><br/><br/><br/>

Reference:
1. pip install issue<br/>
https://stackoverflow.com/questions/56357794/unable-to-install-grpcio-using-pip-install-grpcio
