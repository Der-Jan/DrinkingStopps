from flask import Flask, request, send_file, render_template, jsonify, Response
import os
from werkzeug.utils import secure_filename
import tempfile
from gpx_processor import process_gpx
import json
import logging

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
# Store progress globally (in a real app, use Redis or similar for multiple users)
processing_progress = {"current": 0, "total": 0}

def progress_callback(current, total):
    global processing_progress
    processing_progress["current"] = current
    processing_progress["total"] = total

@app.route('/progress')
def progress():
    def generate():
        while True:
            # Send progress data
            data = {
                "current": processing_progress["current"],
                "total": processing_progress["total"]
            }
            yield f"data: {json.dumps(data)}\n\n"
            # If processing is complete, stop sending updates
            if processing_progress["current"] >= processing_progress["total"] > 0:
                break
    return Response(generate(), mimetype='text/event-stream')

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.endswith('.gpx'):
            try:
                # Reset progress
                global processing_progress
                processing_progress = {"current": 0, "total": 0}
                
                # Save uploaded file
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                file.save(input_path)
                
                # Process the file with progress callback
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced_' + secure_filename(file.filename))
                process_gpx(input_path, output_path, progress_callback)
                
                # Send processed file back to user
                return send_file(output_path, 
                               as_attachment=True, 
                               download_name='enhanced_' + file.filename)
            
            except Exception as e:
                return jsonify({'error': f'Error processing file: {str(e)}'}), 500
            finally:
                # Clean up temporary files
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True) 