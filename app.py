
from flask import Flask, request, jsonify
import os
import json
from execute_model import process_latest_image_to_json  # Import the function for processing the image

app = Flask(__name__)

# Set directories
main_dir = os.getcwd()
input_dir = os.path.join(main_dir, "input")
output_dir = os.path.join(main_dir, "output")

# Ensure input and output directories exist
if not os.path.exists(input_dir):
    os.makedirs(input_dir)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

@app.route('/')
def index():
    return "Welcome to the Image Processing API!"

@app.route('/upload', methods=['POST'])
def upload_image():
    """Upload an image for processing."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Clear the input folder before saving the new file
    for existing_file in os.listdir(input_dir):
        file_path = os.path.join(input_dir, existing_file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Save the uploaded file to the input folder
    file_path = os.path.join(input_dir, file.filename)
    file.save(file_path)

    # Process the image and get the port data
    port_data = process_latest_image_to_json(input_dir, output_dir)

    if "error" in port_data:
        return jsonify(port_data), 400

    # Return the port data as JSON response
    return jsonify(port_data)

@app.route('/get_json', methods=['GET'])
def get_json():
    """Retrieve JSON data of the latest processed image."""
    # Check if the output directory contains files
    if not os.listdir(output_dir):
        return jsonify({"error": "No JSON data available"}), 404

    # Get the most recently created JSON file in the output directory
    latest_json_file = max(
        (os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.json')),
        key=os.path.getctime,
        default=None
    )

    if not latest_json_file:
        return jsonify({"error": "No JSON file found"}), 404

    # Read the JSON file and return its content
    with open(latest_json_file, 'r') as json_file:
        data = json.load(json_file)

    return jsonify(data)  # Send JSON data in response

if __name__ == '__main__':
    app.run(debug=True, port=5000)
