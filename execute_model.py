import os
import cv2
import json
import re
from ultralytics import YOLO

# Load three trained YOLO models
model1 = YOLO('D:/SLT_IMAGE/Model_List/M9/best.pt')  # Model 1
model2 = YOLO('D:/SLT_IMAGE/Model_List/M8/best.pt')  # Model 2
model3 = YOLO('D:/SLT_IMAGE/Model_List/M4/best.pt')  # Model 3

# Load and preprocess the image
def load_image(image_path):
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB for model inference
    return img, img_rgb

# Perform inference with a specific model
def predict_with_model(image_path, model):
    img, img_rgb = load_image(image_path)
    results = model.predict(img_rgb)  # Perform inference
    return results

# Collect port connection information from model predictions
def collect_port_info(results):
    port_info = {i: "not connected" for i in range(1, 9)}  # Default all ports to 'not connected'
    result = results[0]  # Access the first result object
    names_dict = result.names
    boxes = result.boxes.xyxy.cpu().numpy()
    scores = result.boxes.conf.cpu().numpy()
    cls = result.boxes.cls.cpu().numpy()

    for score, cls_id in zip(scores, cls):
        class_name = names_dict[int(cls_id)]
        port_number_match = re.search(r'(\d+)', class_name)
        connection_status_match = re.search(r'(connected|n_connected)', class_name, re.IGNORECASE)

        if port_number_match and connection_status_match:
            port_number = int(port_number_match.group(1))
            connection_status = connection_status_match.group(1).lower()

            if port_number in port_info:
                if connection_status == 'connected':
                    port_info[port_number] = "connected"

    organized_ports = [{"port_number": i, "status": port_info[i]} for i in range(1, 9)]
    return organized_ports

# Combine predictions from multiple models
def combine_results(results_list):
    # Create a dictionary to track the status for each port across all models
    combined_info = {i: [] for i in range(1, 9)}

    for results in results_list:
        port_info = collect_port_info(results)
        for port in port_info:
            combined_info[port["port_number"]].append(port["status"])

    # Apply logic to ensure ports mentioned by at least one model are included
    final_ports = []
    for port_number, statuses in combined_info.items():
        connected_votes = statuses.count("connected")
        not_connected_votes = statuses.count("not connected")
        
        # If at least one model mentions the port, consider its status
        if connected_votes > 0:
            final_status = "connected"
        else:
            final_status = "not connected"

        final_ports.append({"port_number": port_number, "status": final_status})

    return final_ports

# Process only the latest uploaded image
def process_latest_image_to_json(input_folder, output_folder):
    latest_file = max(
        (os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))),
        key=os.path.getctime,
        default=None
    )

    if not latest_file:
        return {"error": "No images found in the input folder"}

    # Perform inference with all models
    results_model1 = predict_with_model(latest_file, model1)
    results_model2 = predict_with_model(latest_file, model2)
    results_model3 = predict_with_model(latest_file, model3)

    # Combine results from all models
    final_ports = combine_results([results_model1, results_model2, results_model3])

    output_data = {
        "image": os.path.basename(latest_file),
        "ports": final_ports
    }

    # Clear old JSON files in the output folder
    for existing_file in os.listdir(output_folder):
        file_path = os.path.join(output_folder, existing_file)
        if file_path.endswith('.json'):
            os.remove(file_path)

    # Save the JSON data to the output directory
    output_file = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(latest_file))[0]}.json")
    with open(output_file, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    return output_data

