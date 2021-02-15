# Cloud

It is a cloud service for file upload/download.

## How to use it

### 0. Prerequisite

add Firebase Admin SDK
```
pip install firebase-admin
```

### 1. Generate private key

Replace serviceAccountKey.json with your key</br>
https://firebase.google.com/docs/admin/setup#initialize-sdk

### 2. Fill in the config

Fill in the bucket name in service.py
```
firebase_admin.initialize_app(cred, {'storageBucket': 'YOUR_STORAGE_BUCKET'})
```

### Note:
1. "Send Media" and "Send Stickers & GIFs" permissions have to be enabled in group
2. sending by URL in sendDocument will currently only work for gif, pdf and zip files
3. bots can download files of up to 20MB in size for the moment
<br/><br/><br/><br/>

Reference:
1. pip install issue<br/>
https://stackoverflow.com/questions/56357794/unable-to-install-grpcio-using-pip-install-grpcio
