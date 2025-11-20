from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import io
import subprocess
import numpy as np
from PIL import Image
from collections import defaultdict
import math
import zipfile
import tempfile
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
BLACK_THRESHOLD = 120
FINAL_SIZE = (3000, 3000)
PPI = 300
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file

# 🔍 Ghostscript path detection
def get_gs_command():
    """Detect Ghostscript command based on OS"""
    if os.name == "nt":
        possible = [
            r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe",
            r"C:\Program Files\gs\gs10.05.0\bin\gswin64c.exe",
            r"C:\Program Files (x86)\gs\gs10.06.0\bin\gswin32c.exe",
        ]
        for path in possible:
            if os.path.isfile(path):
                return path
        return "gswin64c"
    return "gs"

GS_CMD = get_gs_command()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def raster_to_pbm(image_bytes, pbm_path, threshold=BLACK_THRESHOLD):
    """Convert raster image to black/white PBM"""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        data = np.array(img)
        mask = data < threshold
        bw = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8))
        bw.save(pbm_path, format="PPM")
        return True
    except Exception as e:
        print(f"Error in raster_to_pbm: {e}")
        return False

def center_scale_to_canvas(image: Image.Image, size=(3000, 3000), scale_factor=0.85):
    """Center and scale image to fixed canvas size"""
    w, h = image.size
    target_w, target_h = size
    scale = min(target_w / w, target_h / h) * scale_factor
    new_w = int(w * scale)
    new_h = int(h * scale)
    img_resized = image.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("L", size, 255)
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(img_resized, (offset_x, offset_y))
    return canvas

def convert_to_cmyk_eps(input_eps, output_eps):
    """Convert EPS to CMYK color space"""
    try:
        subprocess.run([
            GS_CMD,
            "-dNOPAUSE", "-dBATCH", "-dSAFER",
            "-sDEVICE=eps2write",
            "-dUseCIEColor",
            f"-r{PPI}",
            "-dEPSCrop",
            f"-sOutputFile={output_eps}",
            input_eps
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception as e:
        print(f"Ghostscript error: {e}")
        return False

def check_dependencies():
    """Check if required binaries are available"""
    deps = {}
    try:
        subprocess.run(["potrace", "--version"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        deps['potrace'] = True
    except:
        deps['potrace'] = False
    
    try:
        subprocess.run([GS_CMD, "--version"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        deps['ghostscript'] = True
    except:
        deps['ghostscript'] = False
    
    return deps

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    deps = check_dependencies()
    return jsonify({
        'status': 'healthy',
        'dependencies': deps,
        'ready': all(deps.values())
    })

@app.route('/process', methods=['POST'])
def process_images():
    """Main endpoint to process uploaded images"""
    
    # Check dependencies
    deps = check_dependencies()
    if not all(deps.values()):
        return jsonify({
            'error': 'Missing dependencies',
            'details': deps
        }), 500
    
    # Validate request
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Get options
    threshold = int(request.form.get('threshold', BLACK_THRESHOLD))
    include_eps = request.form.get('include_eps', 'true').lower() == 'true'
    group_by_prefix = request.form.get('group_by_prefix', 'true').lower() == 'true'
    
    # Create temporary working directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        input_dir = os.path.join(temp_dir, 'input')
        temp_bw_dir = os.path.join(temp_dir, 'temp_bw')
        output_svg_dir = os.path.join(temp_dir, 'output_svg')
        output_eps_dir = os.path.join(temp_dir, 'output_eps')
        output_group_dir = os.path.join(temp_dir, 'output_groups')
        
        for d in [input_dir, temp_bw_dir, output_svg_dir, output_eps_dir, output_group_dir]:
            os.makedirs(d, exist_ok=True)
        
        groups = defaultdict(list)
        processed_files = []
        
        # Step 1: Process individual images
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                base_name = os.path.splitext(filename)[0]
                prefix = ''.join([c for c in base_name if not c.isdigit()]).rstrip("_-") or base_name
                
                # Read file
                file_bytes = file.read()
                if len(file_bytes) > MAX_FILE_SIZE:
                    continue
                
                # Convert to PBM
                pbm_path = os.path.join(temp_bw_dir, base_name + ".pbm")
                if not raster_to_pbm(file_bytes, pbm_path, threshold):
                    continue
                
                # Generate SVG
                svg_path = os.path.join(output_svg_dir, base_name + ".svg")
                try:
                    subprocess.run(["potrace", "-s", "-o", svg_path, pbm_path],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                except:
                    continue
                
                # Generate EPS if requested
                if include_eps:
                    raw_eps = os.path.join(output_eps_dir, base_name + "_raw.eps")
                    final_eps = os.path.join(output_eps_dir, base_name + ".eps")
                    
                    try:
                        subprocess.run(["potrace", "-e", "-o", raw_eps, pbm_path],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                        convert_to_cmyk_eps(raw_eps, final_eps)
                        os.remove(raw_eps)
                    except:
                        pass
                
                groups[prefix].append(pbm_path)
                processed_files.append(filename)
        
        # Step 2: Create grouped EPSs if requested
        if group_by_prefix and include_eps:
            for prefix, pbms in groups.items():
                if len(pbms) <= 1:
                    continue
                
                count = len(pbms)
                images = [Image.open(p).convert("L") for p in pbms]
                cols = math.ceil(math.sqrt(count))
                rows = math.ceil(count / cols)
                w, h = images[0].size
                
                composite = Image.new("L", (cols * w, rows * h), 255)
                for idx, img in enumerate(images):
                    r = idx // cols
                    c = idx % cols
                    composite.paste(img, (c * w, r * h))
                
                composite_fixed = center_scale_to_canvas(composite, FINAL_SIZE)
                merged_pbm = os.path.join(temp_bw_dir, f"{prefix}_merged.pbm")
                composite_fixed.save(merged_pbm, format="PPM")
                
                raw_group_eps = os.path.join(output_group_dir, f"{prefix}_final_raw.eps")
                final_group_eps = os.path.join(output_group_dir, f"{prefix}_final.eps")
                
                try:
                    subprocess.run(["potrace", "-e", "-o", raw_group_eps, merged_pbm],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    convert_to_cmyk_eps(raw_group_eps, final_group_eps)
                    os.remove(raw_group_eps)
                except:
                    pass
        
        # Create ZIP file with all outputs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add SVGs
            for filename in os.listdir(output_svg_dir):
                file_path = os.path.join(output_svg_dir, filename)
                zip_file.write(file_path, os.path.join('svg', filename))
            
            # Add individual EPSs
            if include_eps:
                for filename in os.listdir(output_eps_dir):
                    file_path = os.path.join(output_eps_dir, filename)
                    zip_file.write(file_path, os.path.join('eps', filename))
                
                # Add grouped EPSs
                for filename in os.listdir(output_group_dir):
                    file_path = os.path.join(output_group_dir, filename)
                    zip_file.write(file_path, os.path.join('groups', filename))
        
        zip_buffer.seek(0)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='vectorized_outputs.zip'
        )
    
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'Image Vectorization API',
        'endpoints': {
            '/health': 'GET - Check service health',
            '/process': 'POST - Process images (multipart/form-data)'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)