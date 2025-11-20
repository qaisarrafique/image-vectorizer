# 🎨 Image Vectorizer Web Application

Convert raster images (PNG, JPG) to high-quality vector formats (SVG, EPS) with CMYK color space support.

![Status](https://img.shields.io/badge/status-production--ready-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ Features

- 📤 **Drag & Drop Upload** - Simple, intuitive interface
- 🎯 **Adjustable Threshold** - Fine-tune black shape detection (0-255)
- 📐 **Auto-Scaling** - Images centered on 3000×3000px canvas
- 🎨 **CMYK Color Space** - Professional print-ready EPS output
- 🧩 **Smart Grouping** - Automatically groups images by filename prefix
- 📦 **Batch Processing** - Process multiple images simultaneously
- 🔄 **Vector Formats** - Outputs both SVG and EPS
- 📱 **Responsive Design** - Works on desktop and mobile

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Potrace
- Ghostscript

### Installation

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3-pip potrace ghostscript
```

#### On macOS:
```bash
brew install python potrace ghostscript
```

#### On Windows:
Download and install:
- [Python](https://www.python.org/downloads/)
- [Ghostscript](https://www.ghostscript.com/download/gsdnld.html)
- Potrace (compile from source or use WSL)

### Run Locally

1. **Clone/Download this project**
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

2. **Open Frontend**
   - Open `frontend/index.html` in your browser
   - Or use Live Server in VS Code

3. **Process Images**
   - Upload PNG/JPG files
   - Adjust settings
   - Click "Convert to Vector"
   - Download ZIP with results

## 📁 Project Structure

```
image-vectorizer/
├── backend/
│   ├── app.py              # Flask API
│   ├── requirements.txt    # Python packages
│   ├── Dockerfile         # Container config
│   └── render.yaml        # Render deployment
│
├── frontend/
│   ├── index.html         # User interface
│   ├── style.css          # Styling
│   └── script.js          # Frontend logic
│
├── DEPLOYMENT_GUIDE.md    # Hosting instructions
└── README.md              # This file
```

## 🌐 Deployment

### Deploy on Render (Free)

1. **Backend**:
   - Push code to GitHub
   - Create new Web Service on Render
   - Select Docker environment
   - Deploy from repository

2. **Frontend**:
   - Create GitHub repository with `frontend/` files
   - Update `API_URL` in `script.js`
   - Enable GitHub Pages in repository settings

**See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.**

## 🎯 Usage

### Via Web Interface

1. Visit your deployed frontend URL
2. Check green status indicator (🟢)
3. Upload images (drag & drop or click)
4. Configure options:
   - **Threshold**: Lower = more black detected
   - **Include EPS**: Toggle CMYK EPS output
   - **Group by Prefix**: Merge similar filenames
5. Click "Convert to Vector"
6. Download ZIP with results

### API Endpoints

#### Check Health
```bash
GET /health
```
Response:
```json
{
  "status": "healthy",
  "dependencies": {
    "potrace": true,
    "ghostscript": true
  },
  "ready": true
}
```

#### Process Images
```bash
POST /process
Content-Type: multipart/form-data

Parameters:
- files: Image files (PNG/JPG)
- threshold: int (0-255, default: 120)
- include_eps: bool (default: true)
- group_by_prefix: bool (default: true)

Returns: ZIP file with SVG/EPS outputs
```

Example with curl:
```bash
curl -X POST http://localhost:5000/process \
  -F "files=@image1.png" \
  -F "files=@image2.jpg" \
  -F "threshold=120" \
  -F "include_eps=true" \
  -o output.zip
```

## ⚙️ Configuration

### Backend Options

Edit `app.py`:
```python
BLACK_THRESHOLD = 120      # Default threshold
FINAL_SIZE = (3000, 3000)  # Canvas size
PPI = 300                  # DPI for EPS
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
```

### Frontend Options

Edit `script.js`:
```javascript
const API_URL = 'http://localhost:5000';  // Backend URL
```

## 📊 Output Structure

Downloaded ZIP contains:
```
vectorized_outputs.zip
├── svg/
│   ├── image1.svg
│   ├── image2.svg
│   └── ...
├── eps/
│   ├── image1.eps (CMYK)
│   ├── image2.eps (CMYK)
│   └── ...
└── groups/
    ├── prefix1_final.eps
    └── prefix2_final.eps
```

## 🔧 Troubleshooting

### Backend won't start
**Issue**: Dependencies missing  
**Fix**: Install potrace and ghostscript

### Frontend can't connect
**Issue**: Wrong API_URL  
**Fix**: Update `script.js` with correct backend URL

### CORS errors
**Issue**: Cross-origin blocked  
**Fix**: Backend has CORS enabled. Check URL matches.

### Processing timeout
**Issue**: Large files or many images  
**Fix**: Reduce file count or upgrade hosting plan

## 🎨 How It Works

1. **Upload**: User uploads raster images
2. **Threshold**: Convert to black/white at specified threshold
3. **Trace**: Potrace converts bitmap to vector paths
4. **Color**: Ghostscript converts to CMYK color space
5. **Group**: Similar filenames merged into composites
6. **Scale**: All outputs centered on 3000×3000px canvas
7. **Package**: Everything zipped and returned

## 📈 Performance

- **Small images** (<1MB): ~2-5 seconds
- **Medium images** (1-5MB): ~5-15 seconds
- **Large batches** (10+ images): ~20-60 seconds

Free tier limits:
- Render: 512MB RAM, shared CPU
- Consider paid tier for production

## 🔐 Security

- ✅ File type validation
- ✅ File size limits (10MB)
- ✅ Secure filename handling
- ✅ CORS protection
- ✅ No data persistence
- ✅ Automatic cleanup

## 🤝 Contributing

Improvements welcome! Areas to enhance:
- Add more output formats (PDF, AI)
- Real-time preview
- Advanced color space options
- Batch naming templates
- Progress tracking per file

## 📄 License

MIT License - feel free to use and modify.

## 🙏 Credits

- **Potrace**: Vector tracing engine
- **Ghostscript**: PostScript/PDF processing
- **Flask**: Web framework
- **PIL/Pillow**: Image processing

## 📞 Contact

**Developer**: Qaisar Rafique  
**Phone**: 0305-7425107  
**Need customization?** Contact for assistance!

---

**Built with ❤️ for designers, printers, and vector enthusiasts**
