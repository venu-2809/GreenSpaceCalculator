import requests
from PIL import Image
import numpy as np
import cv2

# Mapbox Static Images API parameters
MAPBOX_ACCESS_TOKEN = "ENTER_YOUR_MAPBOX_TOKEN"
MAP_SIZE = "600x400"
ZOOM_LEVEL = 15

# OpenCage Geocoding API parameters
OPENCAGE_API_KEY = "ENTER_YOUR_OPENCAGE_API_KEY"

def get_satellite_image(lon, lat):
    # Use the "satellite-v9" map style for satellite imagery
    base_url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},{ZOOM_LEVEL}/{MAP_SIZE}"
    params = {
        "access_token": MAPBOX_ACCESS_TOKEN,
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return Image.open(requests.get(base_url, params=params, stream=True).raw)
    else:
        print(f"Error: {response.status_code}")
        return None

def get_bounding_box(api_key, location):
    base_url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": location,
        "key": api_key,
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "results" in data and data["results"]:
            bounds = data["results"][0]["bounds"]
            return bounds
        else:
            print("Location not found. Exiting without calculating tree information.")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None

def main_map_segmentation(map_image_path):
    location_name = input("Enter your area name to be accessed:")  # Replace with your desired location
    bounding_box = get_bounding_box(OPENCAGE_API_KEY, location_name)

    if bounding_box:
        lon, lat = (bounding_box["southwest"]["lng"], bounding_box["southwest"]["lat"])
        image = get_satellite_image(lon, lat)

        if image:
            # Convert the PIL Image to a NumPy array
            image_array = np.array(image)

            # Load the segmented image from the map segmentation
            segmented_image = Image.open(map_image_path)
            segmented_array = np.array(segmented_image)

            # Create a binary mask for tree areas
            tree_mask = segmented_array == 255

            # Display the original image with tree areas highlighted
            cv2.imshow("Original Image with Tree Areas", cv2.addWeighted(image_array, 0.7, tree_mask.astype(np.uint8) * 255, 0.3, 0))

            cv2.waitKey(0)
            cv2.destroyAllWindows()

            # Save the modified image with highlighted tree areas
            cv2.imwrite("original_image_with_tree_areas.png", cv2.addWeighted(image_array, 0.7, tree_mask.astype(np.uint8) * 255, 0.3, 0))

            print("Satellite image with highlighted tree areas saved.")

            # Calculate and print the total tree area and free space area
            tree_area, free_space_area = load_calculated_areas("original_image_with_tree_areas.png")
            print(f"Total tree area: {tree_area} square pixels")
            print(f"Total free space area: {free_space_area} square pixels")

            # Calculate the number of trees that can be planted
            num_trees_to_plant = calculate_trees_to_plant(free_space_area)
            print(f"Number of trees that can be planted: {num_trees_to_plant}")

        else:
            print("Failed to get satellite image.")
    else:
        print("Location not found. Exiting without calculating tree information.")

def calculate_trees_to_plant(free_space_area, tree_area_per_tree=100):  
    # Adjust the tree_area_per_tree based on your estimation
    num_trees_to_plant = free_space_area // tree_area_per_tree
    return num_trees_to_plant

def load_calculated_areas(map_image_path):
    # Load the segmented image from the map segmentation
    segmented_image = Image.open(map_image_path)

    # Convert the image to grayscale
    grayscale_image = segmented_image.convert("L")

    # Convert the grayscale image to a NumPy array
    grayscale_array = np.array(grayscale_image)

    # Adaptive thresholding to get binary segmentation
    binary_image = cv2.adaptiveThreshold(grayscale_array, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)

    # Calculate the area of identified trees and free space
    tree_area = np.sum(binary_image == 255)
    free_space_area = np.sum(binary_image == 0)

    return tree_area, free_space_area

def main():
    map_image_path = "original_image_with_tree_areas.png"  # Replace with the path to your generated satellite image

    # Map segmentation
    main_map_segmentation(map_image_path)

if __name__ == "__main__":
    main()
