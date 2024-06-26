import math
import numpy as np
import open3d as o3d
import os
import time
import json

FILENAME = 'lidar_scans.json'

def polar_to_cartesian(distances, translation):
    points = []
    # Count down from 359 to 0 to account for CW rotations versus polar coordinate CCW rotations
    for degree in range(359, 0, -1):
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
    view_ctl.set_front([0.0, 1.0, 0.0])    # 0 -1 0
    view_ctl.set_up([0.0, 0.0, 1.0])        # 0 0 1
    # Adjust the zoom to fit the bounding box
    view_ctl.set_zoom(2.0 / max(extent)) 

def update_translation(translation, distance_traveled, angle_degrees):
    angle_radians = math.radians(angle_degrees)
    translation[0] += distance_traveled * math.cos(angle_radians)
    translation[1] += distance_traveled * math.sin(angle_radians)
    return translation

# Main Function
first_scan = 1
if True:
    print("=== [Beginning Map Program] ===")
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

    data_wait = 0

    # Loop to read data in chunks of three lines
    while True:
        if os.path.exists(FILENAME):
            data_wait = 0
            try:
                with open(FILENAME, 'r') as fp:
                    data = json.load(fp)
            except json.JSONDecodeError:
                continue
            angle = 90
            distance_traveled = float(data["car_distance"])
            distances = data["scans"]
            if distance_traveled != 0 or first_scan == 1:
                # for angle, distance in enumerate(distances):
                #     if angle >= 350 or angle <= 30 or angle >= 160 or angle <= 190:
                #         pass
                #     else:
                #         distances[angle] = 0
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

                # # Adjust view to fit all points
                update_view(vis, pcd)

                # Simulate movement by updating the translation
                translation = update_translation(translation, distance_traveled, angle)
                first_scan = 0
            # elif first_scan == 1:
            #     # Convert to Cartesian coordinates with current translation
            #     new_points = polar_to_cartesian(distances, translation)

            #     # Add new points to the accumulated points
            #     all_points.extend(new_points)

            #     # Create point cloud from all accumulated points
            #     pcd.points = o3d.utility.Vector3dVector(np.array(all_points))
            #     pcd.colors = o3d.utility.Vector3dVector(np.tile([1, 0, 0], (len(all_points), 1)))  # Red color

            #     # Update the visualizer
            #     vis.clear_geometries()
            #     vis.add_geometry(pcd)

            #     # # Adjust view to fit all points
            #     update_view(vis, pcd)

            #     # Simulate movement by updating the translation
            #     translation = update_translation(translation, distance_traveled, angle)
            #     first_scan = 0
            else:
                continue
        else:
            if data_wait == 0:
                print("Waiting for JSON file to populate...")
                data_wait = 1
            time.sleep(0.05)
            continue
