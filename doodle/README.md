# Doodle

It is a web page for drawing

## How to use it

### 0. Prerequisite

Open a project in Firebase</br>
https://console.firebase.google.com/

Create a folder named "Images" under Files in Storage

Apply the following rule under Rules
```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read, write: if request.auth == null;
    }
  }
}
```


### 1. Fill in the config
Fill in the config in index.js
```
var firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_AUTH_DOMAIN",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
};
```

### 2. Host the web page on GitHub
https://pages.github.com/

### 3. Fill in the URL in doodle.py
e.g. https://username.github.io
```
self.STATIC_URL = 'YOUR_URL'
```

### 4. Create a game via BotFather
Create a new game named "doodle"</br>
https://core.telegram.org/bots/api#games

**Make sure "Send Stickers & GIFs" permission is enabled in group!**

<br/><br/><br/><br/>

Reference:
1. Doodle page<br/>
https://github.com/alextechcc/drawgram </br>
https://www.youtube.com/watch?v=3GqUM4mEYKA   

2. Undo function<br/>
https://stackoverflow.com/questions/53960651/how-to-make-an-undo-function-in-canvas

3. Color picker JS library<br/>
http://jillix.github.io/piklor.js/
   
4. Firebase Storage upload image JS<br/>
https://www.youtube.com/watch?v=ZH-PnY-JGBU&t=702s
   
