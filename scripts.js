const MAX_WIDTH = 300;
const MAX_HEIGHT = 300;


function getImageDimensions(file){
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = function() {
      resolve({ width: this.width, height: this.height });
    };
    image.onerror = reject;
    image.src = URL.createObjectURL(file);  // create a blob URL for the File
  });
}


function compressImage(image, scale, initalWidth, initalHeight){
  return new Promise((resolve, reject) => {
      const canvas = document.createElement("canvas");

      canvas.width = scale * initalWidth;
      canvas.height = scale * initalHeight;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      
      ctx.canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error("Blob creation failed"));
        }
      }, "image/png");
  }); 
}


document.getElementById("upload-form").addEventListener("submit", async function(event){
  event.preventDefault();
  const fileInput = document.getElementById("file-input");
  const errorMessage = document.getElementById("file-error");

  if (fileInput.files.length === 0) {
    errorMessage.style.display = "block"; 
    console.log("error")
    return; 
  }
  else {
    errorMessage.style.display = "none"; 
  }

  inputFiles = document.getElementById("file-input").files

  for (const originalFile of inputFiles) {
    const image = new Image();
    image.src = URL.createObjectURL(originalFile);
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = reject;
    });
    
    const { height, width } = { height: image.height, width: image.width };
    
    const widthRatioBlob = await compressImage(image, MAX_WIDTH / width, width, height);
    const heightRatioBlob = await compressImage(image, MAX_HEIGHT / height, width, height);
    
    const thumbnailFile = widthRatioBlob.size > heightRatioBlob.size ? heightRatioBlob : widthRatioBlob;
    
    currentGallery = document.getElementById("current-gallery").innerHTML;
    const formData = new FormData();
    formData.append("originalFile", originalFile);
    formData.append("thumbnailFile", thumbnailFile);
    formData.append("gallery", currentGallery)
    try {
      const response = await fetch("http://127.0.0.1:8000/upload/", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      console.log(data);
    } catch (error) {
      console.error("Upload error:", error);
    }
  }
  window.location.reload();
})


function addFunctions() {
  const imageContainers = document.querySelectorAll(".img-container");

  imageContainers.forEach(function(imageContainer) {
    const deleteButton = imageContainer.querySelector(".delete-button");
    const downloadButton = imageContainer.querySelector(".download-button");
    deleteButton.addEventListener("click", async function() {
      document.body.style.cursor = 'wait';
      const formData = new FormData();
      formData.append("fileName", deleteButton.parentElement.dataset.name);
      formData.append("galleryName", galleryName);
      try {
        const response = await fetch("http://127.0.0.1:8000/delete/", {
          method: "DELETE",
          body: formData
        });
        const data = await response.json();
        window.location.reload();
      } catch (error) {
        console.error("Upload error:", error);
      }
    })
    imageContainer.addEventListener("click", function() {
      imageContainer.classList.remove("unclicked");
      deleteButton.style.display = "block";
      downloadButton.style.display = "block";
    });
    imageContainer.addEventListener("mouseleave", function() {
      imageContainer.classList.add("unclicked");
      deleteButton.style.display = "none";
      downloadButton.style.display = "none";
    });
  });
}


async function loadGallery(name) {
  document.getElementById("current-gallery").innerHTML = name;

  const gallery = document.getElementById("gallery");
  gallery.innerHTML = "";

  const response = await fetch(`http://127.0.0.1:8000/show?gallery=${encodeURIComponent(name)}`);
  
  const imageUrls = await response.json();
  imageUrls.forEach(url => {
    const img = document.createElement("img");
    const parts = url.split('/').pop();
    const name = parts.split('.')[0];
    img.src = url;
    img.loading = "lazy";
    
    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.classList.add("delete-button");

    const downloadButton = document.createElement("button");
    downloadButton.textContent = "Download";
    downloadButton.classList.add("download-button");

    const buttons = document.createElement("div");
    buttons.appendChild(downloadButton);
    buttons.appendChild(deleteButton);
    buttons.classList.add("buttons");
    buttons.setAttribute("data-name", name);
    
    const imgContainer = document.createElement("div");
    imgContainer.classList.add("img-container");
    imgContainer.classList.add("unclicked");
    imgContainer.appendChild(img);
    imgContainer.appendChild(buttons);

    gallery.appendChild(imgContainer);
  });

  const spacer = document.createElement("div");
  spacer.classList.add("gallery-spacer");
  gallery.appendChild(spacer);

  addFunctions();
}


document.getElementById("choose-gallery").addEventListener("submit", async function(event){
  event.preventDefault();
  const inputGallery = document.getElementById("name-choose").value
  if (inputGallery) {
    const currentGallery = localStorage.getItem("currentGallery");
    var chosenGallery = "";
    if (currentGallery == inputGallery) {
      chosenGallery = currentGallery;
    }
    else { 
      chosenGallery = document.getElementById("name-choose").value;
    }
    localStorage.setItem("currentGallery", chosenGallery);
    loadGallery(chosenGallery);
  }
})  


const galleryName = localStorage.getItem("currentGallery");
if (galleryName) {
  loadGallery(galleryName);
}


function updateFileUploadButton(element, text_element, upload_element, fileNum) {
  const drop_zone = document.getElementById(element);
  drop_zone.classList.add('disabled');
  const text = document.getElementById(text_element);
  if (fileNum == 1) {
    text.innerHTML = `A file was uploaded.`;
  }
  else {
    text.innerHTML = `${fileNum} files were uploaded.`;
  }
  const upload = document.getElementById(upload_element);
  upload.style.display = "none";
}


function dragOverHandler(event) {
  event.preventDefault();
}


function dropHandler(event) {
  event.preventDefault();
  const dataTransfer = new DataTransfer();
  if (event.dataTransfer.items) {
    [...event.dataTransfer.items].forEach((item, i) => {
      if (item.kind === "file") {
        const file = item.getAsFile();
        dataTransfer.items.add(file);
      }
    });
  }
  const input = document.getElementById("file-input");
  input.files = dataTransfer.files;
  updateFileUploadButton("drop-zone", "text", "upload", event.dataTransfer.items.length)
}

function addFile(event) {
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.required = true;
  input.onchange = e => {   
    const dataTransfer = new DataTransfer();
    for (const file of e.target.files) {
      dataTransfer.items.add(file);
    }
    const input = document.getElementById("file-input");
    input.files = dataTransfer.files;
    updateFileUploadButton("drop-zone", "text", "upload", e.target.files.length);
  }
  input.click();
}


function resetFiles(event) {
  const dropZone = document.getElementById("drop-zone");
  dropZone.classList.remove("disabled");
  const text = document.getElementById("text");
  text.innerHTML = "Drag your original file here.";
  const upload = document.getElementById("upload");
  upload.style.display = "block";
}
