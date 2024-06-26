import math
import numpy as np

import math
import numpy as np
import open3d as o3d
import time

def parse_data(input_str):
    try:
        # Split the line into two parts: angle-distance and distances array
        parts = input_str.split(' ', 1)  # Split only at the first space
        if len(parts) < 2:
            print(f"Invalid input format: {input_str}")
            return None, None, None
        
        # Extract and parse the angle and distance travelled
        angle_distance_str = parts[0].strip('{}')
        angle_distance_parts = angle_distance_str.split(',')
        
        if len(angle_distance_parts) < 2:
            print(f"Invalid angle-distance format: {angle_distance_str}")
            return None, None, None
        
        angle = float(angle_distance_parts[0])
        distance_travelled = float(angle_distance_parts[1])
        
        # Extract and parse the distances array
        distances_str = parts[1].strip('[]').strip()
        if not distances_str:
            print(f"Empty distances array: {input_str}")
            return angle, distance_travelled, []
        
        distances = list(map(float, distances_str.split(',')))
        return angle, distance_travelled, distances
    except Exception as e:
        print(f"Error parsing input data: {e}")
        print(f"Input string causing error: {input_str}")
        return None, None, None

def polar_to_cartesian(distances, translation):
    points = []
    for degree in range(360):
        if degree < len(distances):
            distance = distances[degree]
            if distance == 0:
                continue  # Skip zero distances
            radians = math.radians(degree)
            x = distance * math.cos(radians) + translation[0]
            y = distance * math.sin(radians) + translation[1]
            z = 0  # Assuming 2D LiDAR
            points.append([x, y, z])
    return np.array(points)

def create_point_cloud(points, color):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(np.tile(color, (points.shape[0], 1)))
    return pcd

def update_view(vis, pcd):
    vis.update_geometry(pcd)
    vis.poll_events()
    vis.update_renderer()

    # Fit the view to the new set of points
    view_ctl = vis.get_view_control()
    bounds = pcd.get_axis_aligned_bounding_box()
    center = bounds.get_center()
    extent = bounds.get_extent()

    # Set the lookat point to the center of the bounding box
    view_ctl.set_lookat(center)
    # Set the front to a reasonable direction
    view_ctl.set_front([0.0, 0.0, -1.0])
    # Set the up direction
    view_ctl.set_up([0.0, 1.0, 0.0])
    # Adjust the zoom to fit the bounding box
    view_ctl.set_zoom(2.0 / max(extent))  # Adjust this factor as needed

def update_translation(translation, distance_traveled, angle_degrees):
    angle_radians = math.radians(angle_degrees)
    translation[0] += distance_traveled * math.cos(angle_radians)
    translation[1] += distance_traveled * math.sin(angle_radians)
    return translation

def process_and_display(filename):
    # Initialize Open3D visualizer with specific window dimensions
    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name='LiDAR Point Cloud', width=800, height=600)

    # Initial translation
    translation = [0, 0, 0]
    # Store all points
    all_points = []

    # Create an empty point cloud object for initial visualization
    pcd = o3d.geometry.PointCloud()
    vis.add_geometry(pcd)

    # Read and process each line in the file
    with open(filename, 'r') as file:
        lines = file.readlines()

    try:
        for i, line in enumerate(lines):
            line = line.strip()
            print(f"Processing line {i + 1}: {line}")
            angle, distance_travelled, distances = parse_data(line)

            if angle is not None and distance_travelled is not None and distances is not None:
                print(f"Line {i + 1} Parsed Angle: {angle}")
                print(f"Line {i + 1} Parsed Distance Travelled: {distance_travelled}")
                print(f"Line {i + 1} Parsed Distances Array: {distances}")
                print()

                # Convert to Cartesian coordinates with current translation
                new_points = polar_to_cartesian(distances, translation)

                # Add new points to the accumulated points
                all_points.extend(new_points)

                # Create point cloud from all accumulated points
                pcd.points = o3d.utility.Vector3dVector(np.array(all_points))
                pcd.colors = o3d.utility.Vector3dVector(np.tile([1, 0, 0], (len(all_points), 1)))  # Red color

                # Update the visualizer
                vis.clear_geometries()
                vis.add_geometry(pcd)

                # Adjust view to fit all points
                update_view(vis, pcd)

                # Simulate movement by updating the translation
                translation = update_translation(translation, distance_travelled, angle)

                # Wait for 1 second before the next update
                time.sleep(1)
            else:
                print(f"Failed to parse data on line {i + 1}")

    except KeyboardInterrupt:
        # Close the visualizer on interrupt
        vis.destroy_window()

# Example usage
filename = 'data.txt'
process_and_display(filename)

