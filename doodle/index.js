var firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_AUTH_DOMAIN",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
};
firebase.initializeApp(firebaseConfig);
//db = firebase.firestore();
db = firebase.storage();

var clipboard = new ClipboardJS('.clip');

const canvas = document.getElementById('paint');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

//fill transparent background
ctx.fillStyle = "white";
ctx.fillRect(0, 0, canvas.width, canvas.height);
	
ctx.lineJoin = 'round';
ctx.lineCap = 'round';
ctx.strokeStyle = "#3498db";
let drawing = false;
let pathsry = [];
let points = [];
let dotSize = 6;
let dotSizeBefore = 6;

var mouse = {x: 0, y: 0};
var previous = {x: 0, y: 0};

attachListeners();

//Mouse Event START
function onMouseDown(e) {
	drawing = true;	
	previous = {x: mouse.x, y: mouse.y};
	mouse = oMousePos(canvas, e);
	points = [];
	points.push({x: mouse.x, y: mouse.y})

	//draw a point
	ctx.beginPath();
    ctx.arc(e.clientX, e.clientY, dotSize/2, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
	//--
}

function onMouseUp(e) {
	drawing = false;
	// Adding the path to the array or the paths
	pathsry.push(points);
}

function onMouseMove(e) {
	if(drawing){
		previous = {x: mouse.x, y: mouse.y};
		mouse = oMousePos(canvas, e);
		// saving the points in the points array
		points.push({x: mouse.x, y: mouse.y, color: color, dotSize: dotSize})
		// drawing a line from the previous point to the current point
		ctx.beginPath();
		ctx.moveTo(previous.x, previous.y);
		ctx.lineTo(mouse.x, mouse.y);
		ctx.lineWidth = dotSize;
		ctx.lineJoin = 'round';
		ctx.lineCap = 'round';
        ctx.strokeStyle = color;
		ctx.stroke();
	}
}
//Mouse Event END


//Touch Event START
function onTouchStart(e) {
    preventTouchClick(e);
    canvas.dispatchEvent(new MouseEvent('mousedown', {
        clientX: e.touches[0].clientX,
        clientY: e.touches[0].clientY
    }));
}

function onTouchEnd(e) {
    preventTouchClick(e);
    canvas.dispatchEvent(new MouseEvent('mouseup', {}));
}

function onTouchMove(e) {
    preventTouchClick(e);
    canvas.dispatchEvent(new MouseEvent('mousemove', {
        clientX: e.touches[0].clientX,
        clientY: e.touches[0].clientY
    }));
}

function preventTouchClick(e) {
    if (e.target === canvas) {
        e.preventDefault();
    }
}
//Touch Event END



function drawPaths(){
	//delete everything
	ctx.clearRect(0, 0, canvas.width, canvas.height);
	
	//draw all the paths in the paths array
	pathsry.forEach(path => {
		if (path.length==1){
			//draw a point
			ctx.beginPath();
			ctx.arc(path[0].x, path[0].y, dotSize/2, 0, Math.PI * 2);
			ctx.fillStyle = color;
			ctx.fill();
			//--
		}else{
			ctx.beginPath();
			ctx.moveTo(path[0].x, path[0].y);  
			for(let i = 1; i < path.length; i++){
				ctx.lineTo(path[i].x,path[i].y);
				ctx.lineWidth = path[i].dotSize;
				ctx.lineJoin = 'round';
				ctx.lineCap = 'round';
				ctx.strokeStyle = path[i].color;
			}
			ctx.stroke();
		}
	})
}  

function Undo(){
  // remove the last path from the paths array
  pathsry.splice(-1,1);
  // draw all the paths in the paths array
  drawPaths();
}


// a function to detect the mouse position
function oMousePos(canvas, evt) {
	var ClientRect = canvas.getBoundingClientRect();
	return { //objeto
		x: Math.round(evt.clientX - ClientRect.left),
		y: Math.round(evt.clientY - ClientRect.top)
	}
}


function submitButton() {
    temp_canvas = document.createElement('canvas');
    temp_canvas.width = canvas.width;
    temp_canvas.height = canvas.height;
    temp_vctx = temp_canvas.getContext('2d');
	
	//fill transparent background
	temp_vctx.fillStyle = "white";
	temp_vctx.fillRect(0, 0, temp_canvas.width, temp_canvas.height);

    temp_vctx.drawImage(canvas, 0, 0, temp_canvas.width, temp_canvas.height);	
    temp_canvas.toBlob(submit, 'image/png', 0.1);
}

function submit(imgBlob) {
    console.log("Submitting");

	var imageElement = document.getElementById("image");
	document.getElementById("color-picker-wrapper").style.display = "none";
    document.getElementById("color").style.display = "none";
	document.getElementById("small-dot").style.display = "none";
	document.getElementById("medium-dot").style.display = "none";
	document.getElementById("large-dot").style.display = "none";
	document.getElementById("eraser").style.display = "none";
	document.getElementById("undo").style.display = "none";
	document.getElementById("clear").style.display = "none";
	document.getElementById("tick").style.display = "none";
	document.getElementById("paint").style.display = "none";
	
	var filename = getId()+'.png';
	var uploadTask = db.ref('Images/'+filename).put(new File([imgBlob], filename));
	uploadTask.then((snapshot) => {
		snapshot.ref.getDownloadURL().then(function(url){
			imageElement.style.maxHeight = "auto";
			imageElement.style.maxWidth = "auto";
			console.log(window.innerHeight);
			console.log(window.innerWidth);
			//imageElement.src = URL.createObjectURL(imgBlob);
            imageElement.src = url;
			imageElement.style.display = "block";
			var copyElement = document.getElementById("copy");
			copyElement.setAttribute('data-clipboard-text', url);
			copyElement.style.display = "block";
		});
	});
	detachListeners();
}

function getId(){
	var now = new Date();
	return now.getSeconds().toString() + now.getMilliseconds().toString();
}

function setActive(ele){
	var current = document.getElementsByClassName("active");
	console.log(current.length);
	current[0].className = current[0].className.replace(" active", "");
	ele.className += " active";
}

function attachListeners() {
    // Drawing buttons
    document.getElementById('small-dot').onmousedown = (e) => {
		dotSize = 3;
		dotSizeBefore = dotSize;
		color=document.getElementById('color').getAttribute('value');
		setActive(e.srcElement);
	};
    document.getElementById('medium-dot').onmousedown = (e) => {
		dotSize = 6;
		dotSizeBefore = dotSize;
		color=document.getElementById('color').getAttribute('value');
		setActive(e.srcElement);
	};
    document.getElementById('large-dot').onmousedown = (e) => {
		dotSize = 10;
		dotSizeBefore = dotSize;
		color=document.getElementById('color').getAttribute('value');
		setActive(e.srcElement);
	};
	document.getElementById('eraser').onmousedown = (e) => {
		dotSizeBefore = dotSize; 
		dotSize = 30; 
		color = 'white';
		setActive(e.srcElement);
	};
	document.getElementById('undo').onmousedown = Undo;
	document.getElementById('clear').onmousedown = () => {
		ctx.clearRect(0, 0, canvas.width, canvas.height);
		pathsry = [];
		points = [];
	};
    document.getElementById('tick').onmousedown = submitButton;

    // Drawing event handlers (bound to mouse, redirected from touch)
    canvas.addEventListener('mousedown', onMouseDown, false);
    canvas.addEventListener('mouseup', onMouseUp, false);
    canvas.addEventListener('mousemove', onMouseMove, false);

    // Touch event redirect
    canvas.addEventListener('touchstart', onTouchStart, false);
    canvas.addEventListener('touchend', onTouchEnd, false);
    canvas.addEventListener('touchcancel', onTouchEnd, false);
    canvas.addEventListener('touchmove', onTouchMove, false);

    // Dynamic canvas size
    window.addEventListener('resize', resizeCanvas, false);
    window.addEventListener("load", init, false);
}


function init() {
    color = document.getElementById('color').getAttribute('value');
    resizeCanvas();
	
	var pk = new Piklor(".color-picker", [
	        "#e74c3c"
          , "#f39c12"
          , "#f1c40f"
          , "#2ecc71"
          , "#1abc9c"
          , "#3498db"
          , "#9b59b6"
          , "#34495e"
          , "#82eedd"
          , "#16a085"
          , "#27ae60"
          , "#2980b9"
          , "#8e44ad"
          , "#2c3e50"
          , "#e67e22"
          , "#95a5a6"
          , "#d35400"
          , "#c0392b"
          , "#bdc3c7"
          , "#7f8c8d"
		  , "#ffc0cb"
        ], {
            open: ".color-picker-wrapper .color-icon"
        })
      , colorIcon = pk.getElm(".color-icon")
      ;

    pk.colorChosen(function (col) {
        colorIcon.style.backgroundColor = col;
		colorIcon.setAttribute("value", col);
		color = col;
		dotSize = dotSizeBefore;
    });
	
}

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}


function detachListeners() {
    document.getElementById('small-dot').onmousedown = null;
    document.getElementById('medium-dot').onmousedown = null;
    document.getElementById('large-dot').onmousedown = null;
	document.getElementById('eraser').onmousedown = null;
    document.getElementById('undo').onmousedown = null;
	document.getElementById('clear').onmousedown = null;
    document.getElementById('tick').onmousedown = null;
    canvas.removeEventListener('mousedown', onMouseDown, false);
    canvas.removeEventListener('mouseup', onMouseUp, false);
    canvas.removeEventListener('mousemove', onMouseMove, false);
    canvas.removeEventListener('touchstart', onTouchStart, false);
    canvas.removeEventListener('touchend', onTouchEnd, false);
    canvas.removeEventListener('touchcancel', onTouchEnd, false);
    canvas.removeEventListener('touchmove', onTouchMove, false);
    window.removeEventListener('resize', resizeCanvas, false);
    window.removeEventListener("load", init, false);
}