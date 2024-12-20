from flask import Flask, request, send_file, render_template
import os
from werkzeug.utils import secure_filename
import tempfile
from gpx_processor import process_gpx

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
        
        if file and file.filename.endswith('.gpx'):
            try:
                # Save uploaded file
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                file.save(input_path)
                
                # Process the file
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced_' + secure_filename(file.filename))
                process_gpx(input_path, output_path)
                
                # Send processed file back to user
                return send_file(output_path, 
                               as_attachment=True, 
                               download_name='enhanced_' + file.filename)
            
            except Exception as e:
                return f'Error processing file: {str(e)}', 500
            finally:
                # Clean up temporary files
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
        
        return 'Invalid file type', 400
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True) 