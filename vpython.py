from vpython import *
from time import *

b = 0
a = 10
distance_threshold = 50  # Distance at which the road will turn to -x direction
x_distance_threshold = 30  # Distance at which the road will turn back to -z direction
z_distance_threshold = 100  # Extended length for the 3rd road

# Initial straight road
path1 = box(pos=vector(0, -5, 0), size=vector(10, 0.5, 15), color=color.white)
camp = box(pos=vector(-10, 0, 0), size=vector(10, 10, 15), color=color.red)
door = box(pos=vector(-6.6, -1.5, 0), size=vector(4, 7, 4), color=color.black)

# Placeholder for the new road segments
path2 = None
path3 = None
path4 = None
started_new_road_x = False
started_new_road_z = False
started_new_road_x2 = False

while True:
    rate(5)
    
    if a <= distance_threshold:
        # Growing the initial straight road along the z-axis
        path1.size.z = a
        path1.pos.z = b - (a / 2) + 5  # Adjust the position to expand in -z direction only
    elif not started_new_road_x:
        # Create the new road segment when the straight road reaches the threshold
        path2 = box(pos=vector(path1.pos.x - 5, path1.pos.y, path1.pos.z - (a / 2) + 5), size=vector(15, 0.5, 10), color=color.white)
        started_new_road_x = True  # Ensure the new road is only created once

    if started_new_road_x:
        # Growing the new road in the -x direction
        if path2.size.x < x_distance_threshold:
            path2.size.x = a - distance_threshold  # Increase the length in the -x direction
            path2.pos.x = path1.pos.x - (a - distance_threshold) / 2  # Adjust the position to expand in -x direction
        else:
            # Stop expanding in -x direction and adjust size to x_distance_threshold
            path2.size.x = x_distance_threshold

            if not started_new_road_z:
                # Create the new road segment that expands back in -z direction from the end of path2
                path3 = box(pos=vector(path2.pos.x - 15 / 2, path2.pos.y, path2.pos.z), size=vector(15, 0.5, 10), color=color.white)
                started_new_road_z = True  # Ensure the new road is only created once

        if started_new_road_z:
            # Growing the new road in the -z direction, extending it with the new threshold
            if path3.size.z < z_distance_threshold:
                path3.size.z = (a - distance_threshold) - x_distance_threshold  # Continue expanding in the -z direction
                path3.pos.z = path2.pos.z - ((a - distance_threshold) - x_distance_threshold) / 2  # Adjust the position to expand in -z direction
            else:
                path3.size.z = z_distance_threshold  # Final size of the 3rd road

                if not started_new_road_x2:
                    # Create the 4th road expanding in the +x direction from the end of path3
                    path4 = box(pos=vector(path3.pos.x + 15 / 2, path3.pos.y, path3.pos.z - z_distance_threshold / 2), size=vector(10, 0.5, 15), color=color.white)
                    started_new_road_x2 = True  # Ensure the 4th road is only created once

        if started_new_road_x2:
            # Growing the 4th road in the +x direction
            path4.size.x = a - (distance_threshold + x_distance_threshold + z_distance_threshold)  # Continue expanding in the +x direction
            path4.pos.x = path3.pos.x + ((a - (distance_threshold + x_distance_threshold + z_distance_threshold)) / 2)  # Adjust the position to expand in +x direction

    a += 1  # Increment the length for all roads