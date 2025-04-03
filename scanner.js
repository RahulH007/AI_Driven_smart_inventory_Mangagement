// Scanner functionality
let stream = null;
let currentUPC = null;
let currentItemData = null;
let codeReader = null;
let cv = null; // OpenCV.js instance

// Initialize Firebase
const firebaseConfig = {
    apiKey: "AIzaSyDxGXQZQZQZQZQZQZQZQZQZQZQZQZQZQZQ",
    authDomain: "kirana-store-manager.firebaseapp.com",
    projectId: "kirana-store-manager",
    storageBucket: "kirana-store-manager.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:abcdef1234567890"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();

// DOM Elements
let startCameraBtn;
let captureImageBtn;
let barcodeUpload;
let processUploadBtn;
let cameraFeed;
let barcodeCanvas;
let scanResult;
let upcResult;
let itemDetails;
let addToInventoryBtn;
let scanError;
let scanLoading;
let cameraPlaceholder;

// Initialize scanner elements and OpenCV
async function initializeScannerElements() {
    console.log('Initializing scanner elements...');
    
    try {
        startCameraBtn = document.getElementById('start-camera');
        captureImageBtn = document.getElementById('capture-image');
        barcodeUpload = document.getElementById('barcode-upload');
        processUploadBtn = document.getElementById('process-upload');
        cameraFeed = document.getElementById('camera-feed');
        barcodeCanvas = document.getElementById('barcode-canvas');
        scanResult = document.getElementById('scan-result');
        upcResult = document.getElementById('upc-result');
        itemDetails = document.getElementById('item-details');
        addToInventoryBtn = document.getElementById('add-to-inventory');
        scanError = document.getElementById('scan-error');
        scanLoading = document.getElementById('scan-loading');
        cameraPlaceholder = document.getElementById('camera-placeholder');

        console.log('DOM elements initialized');

        // Load OpenCV.js
        await loadOpenCV();
        
        // Initialize ZXing as fallback
        await initializeZXing();

        // Add event listeners
        if (startCameraBtn) {
            startCameraBtn.addEventListener('click', startCamera);
        }
        if (captureImageBtn) {
            captureImageBtn.addEventListener('click', captureImage);
        }
        if (processUploadBtn) {
            processUploadBtn.addEventListener('click', processUpload);
        }
        if (addToInventoryBtn) {
            addToInventoryBtn.addEventListener('click', addToInventory);
        }
        if (barcodeUpload) {
            barcodeUpload.addEventListener('change', handleFileUpload);
        }

    } catch (error) {
        console.error('Error initializing scanner:', error);
    }
}

// Load OpenCV.js
function loadOpenCV() {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://docs.opencv.org/4.8.0/opencv.js';
        script.onload = () => {
            cv = window.cv;
            console.log('OpenCV.js loaded successfully');
            resolve();
        };
        script.onerror = () => {
            console.error('Failed to load OpenCV.js');
            reject(new Error('Failed to load OpenCV.js'));
        };
        document.head.appendChild(script);
    });
}

// Initialize ZXing library
async function initializeZXing() {
    try {
        // Wait for ZXing to be available
        let attempts = 0;
        while (typeof window.ZXing === 'undefined' && attempts < 10) {
            await new Promise(resolve => setTimeout(resolve, 500));
            attempts++;
        }

        if (typeof window.ZXing === 'undefined') {
            throw new Error('ZXing library not available after waiting');
        }

        console.log('Initializing ZXing reader...');
        codeReader = new window.ZXing.BrowserMultiFormatReader();
        
        // Configure hints for better barcode detection
        const hints = new Map();
        hints.set(window.ZXing.DecodeHintType.POSSIBLE_FORMATS, [
            window.ZXing.BarcodeFormat.EAN_13,
            window.ZXing.BarcodeFormat.EAN_8,
            window.ZXing.BarcodeFormat.UPC_A,
            window.ZXing.BarcodeFormat.UPC_E,
            window.ZXing.BarcodeFormat.CODE_128,
            window.ZXing.BarcodeFormat.CODE_39
        ]);
        hints.set(window.ZXing.DecodeHintType.TRY_HARDER, true);
        codeReader.hints = hints;

        // Add event listeners
        if (startCameraBtn) {
            console.log('Adding click listener to start camera button');
            startCameraBtn.addEventListener('click', startCamera);
        }
        
        if (captureImageBtn) {
            captureImageBtn.addEventListener('click', captureImage);
        }
        
        if (processUploadBtn) {
            processUploadBtn.addEventListener('click', processUpload);
        }
        
        if (addToInventoryBtn) {
            addToInventoryBtn.addEventListener('click', addToInventory);
        }

        console.log('Scanner initialization complete');
    } catch (error) {
        console.error('Error initializing ZXing:', error);
        alert('Error initializing barcode scanner. Please refresh the page and try again.');
    }
}

// Start camera
async function startCamera() {
    try {
        console.log('Starting camera...');
        
        // Stop any existing stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }

        // Request camera access
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'environment',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        });

        // Set up video stream
        cameraFeed.srcObject = stream;
        cameraPlaceholder.style.display = 'none';
        cameraFeed.style.display = 'block';
        startCameraBtn.style.display = 'none';
        captureImageBtn.style.display = 'flex';

        console.log('Camera started successfully');
    } catch (error) {
        console.error('Error starting camera:', error);
        alert('Failed to access camera. Please ensure camera permissions are granted.');
    }
}

// Capture image from camera
async function captureImage() {
    if (!stream) {
        alert('Please start the camera first');
        return;
    }

    try {
        const canvas = document.createElement('canvas');
        canvas.width = cameraFeed.videoWidth;
        canvas.height = cameraFeed.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(cameraFeed, 0, 0);
        
        // Convert to blob and process
        canvas.toBlob(blob => {
            const file = new File([blob], 'captured-barcode.jpg', { type: 'image/jpeg' });
            processImage(file);
        }, 'image/jpeg');
    } catch (error) {
        console.error('Error capturing image:', error);
        alert('Failed to capture image');
    }
}

// Process uploaded image
async function processUpload() {
    const file = barcodeUpload.files[0];
    if (!file) {
        alert('Please select an image first');
        return;
    }
    await processImage(file);
}

// Process image function
async function processImage(file) {
    try {
        showLoading(true);
        
        // Create FormData to send the image
        const formData = new FormData();
        formData.append('image', file);
        
        // Send to backend API
        const response = await fetch('/api/barcode/scan', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to process image');
        }
        
        const data = await response.json();
        
        if (data.barcode) {
            currentUPC = data.barcode;
            upcResult.textContent = `UPC: ${data.barcode}`;
            
            // Look up item details
            const itemData = await lookupUPC(data.barcode);
            if (itemData) {
                currentItemData = itemData;
                displayItemDetails(itemData);
                scanResult.style.display = 'block';
                scanError.style.display = 'none';
            } else {
                throw new Error('Item not found');
            }
        } else {
            throw new Error('No barcode detected');
        }
    } catch (error) {
        console.error('Error processing image:', error);
        scanError.style.display = 'block';
        scanResult.style.display = 'none';
    } finally {
        showLoading(false);
    }
}

// Handle file upload
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        processUploadBtn.disabled = false;
    }
}

// Show loading state
function showLoading(show) {
    scanLoading.style.display = show ? 'flex' : 'none';
}

// Reset scanner
function resetScanner() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    cameraFeed.srcObject = null;
    cameraPlaceholder.style.display = 'flex';
    cameraFeed.style.display = 'none';
    startCameraBtn.style.display = 'flex';
    captureImageBtn.style.display = 'none';
    scanResult.style.display = 'none';
    scanError.style.display = 'none';
    currentUPC = null;
    currentItemData = null;
    barcodeUpload.value = '';
    processUploadBtn.disabled = true;
}

// Initialize scanner when the page is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the scanner page
    if (document.getElementById('scanner-page')) {
        initializeScannerElements();
    }
});

// Re-initialize scanner when switching to the scanner page
window.addEventListener('showPage', (event) => {
    if (event.detail === 'scanner') {
        resetScanner();
        setTimeout(initializeScannerElements, 100);
    }
});

// Handle barcode detection
async function handleBarcodeDetected(barcode) {
    try {
        showLoading(true);
        currentUPC = barcode;
        upcResult.textContent = `UPC: ${barcode}`;
        
        // Look up item details
        const itemData = await lookupUPC(barcode);
        if (itemData) {
            currentItemData = itemData;
            displayItemDetails(itemData);
            scanResult.style.display = 'block';
            scanError.style.display = 'none';
        } else {
            throw new Error('Item not found');
        }
    } catch (error) {
        console.error('Error handling barcode:', error);
        scanError.style.display = 'block';
        scanResult.style.display = 'none';
    } finally {
        showLoading(false);
    }
}

// Lookup UPC using the API
async function lookupUPC(upc) {
    try {
        // First try to get from Firebase
        const itemRef = db.collection('inventory').doc(upc);
        const doc = await itemRef.get();
        
        if (doc.exists) {
            return doc.data();
        }
        
        // If not in Firebase, try external API
        const response = await fetch(`https://world.openfoodfacts.org/api/v0/product/${upc}.json`);
        const data = await response.json();
        
        if (data.status === 1 && data.product) {
            return {
                name: data.product.product_name || 'Unknown Product',
                brand: data.product.brands || 'Unknown Brand',
                quantity: data.product.quantity || 'N/A',
                image: data.product.image_url || null
            };
        }
        return null;
    } catch (error) {
        console.error('Error looking up UPC:', error);
        return null;
    }
}

// Display item details
function displayItemDetails(item) {
    itemDetails.innerHTML = `
        <p><strong>Name:</strong> ${item.name}</p>
        <p><strong>Brand:</strong> ${item.brand}</p>
        <p><strong>Quantity:</strong> ${item.quantity}</p>
        ${item.image ? `<img src="${item.image}" alt="${item.name}" style="max-width: 200px;">` : ''}
    `;
    scanResult.style.display = 'block';
}

// Add item to Firebase inventory
async function addToInventory() {
    if (!currentUPC || !currentItemData) {
        alert('Please scan a valid barcode first');
        return;
    }

    try {
        showLoading(true);
        const itemRef = db.collection('inventory').doc(currentUPC);
        await itemRef.set({
            upc: currentUPC,
            name: currentItemData.name,
            brand: currentItemData.brand,
            quantity: currentItemData.quantity,
            image: currentItemData.image,
            lastUpdated: firebase.firestore.FieldValue.serverTimestamp()
        });
        alert('Item added to inventory successfully!');
        resetScanner();
    } catch (error) {
        console.error('Error adding to inventory:', error);
        alert('Failed to add item to inventory');
    } finally {
        showLoading(false);
    }
} 