import os 
import json
import numpy as np
from PIL import Image
vertices = []
faces = []
textures = []
FOV = 90
NEAR = 0.1
FAR = 100
IMAGE_WIDTH = 512
IMAGE_HEIGHT = 512
buffer = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8)
depth_buffer = np.full((IMAGE_HEIGHT, IMAGE_WIDTH), np.inf)
# projection matrix that scales based on the field of view and aspect ratio
def create_projection_matrix(fov, aspect_ratio, near, far):
    scale = 1.0 / np.tan(np.radians(fov) / 2)
    projection_matrix = np.zeros((4, 4))
    projection_matrix[0, 0] = scale
    projection_matrix[1, 1] = scale
    projection_matrix[2, 2] = -far / (far - near)
    projection_matrix[2, 3] = -1
    projection_matrix[3, 2] = -far * near / (far - near)

    return projection_matrix
def load_obj(file_path): 
    
    try: 
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('v '):
                    vertex = list(map(float, line.strip().split()[1:]))
                    vertices.append(vertex)
                if line.startswith('f '):
                    face = line.strip().split()
                    textures = [int(i.split('/')[1]) - 1 for i in face[1:]]
                    face = [int(i.split('/')[0]) - 1 for i in face[1:]]
                    faces.append(face)
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
def homogeneous_to_cartesian(vertex):
    if vertex[3] != 1:
        vertex[0] /= vertex[3]
        vertex[1] /= vertex[3]
        vertex[2] /= vertex[3]
        vertex[3] = 1
    return vertex[:4]

def camera_to_raster(vertex, world_to_camera, projection):
    vertex_homogeneous = np.array(vertex + [1])
    # print(vertex_homogeneous)
    camera_space_vertex = np.matmul(vertex_homogeneous, world_to_camera)
    camera_space_vertex = homogeneous_to_cartesian(camera_space_vertex)
    # project from camera space to clip space
    projected_vertex = np.matmul(camera_space_vertex, projection)
    # convert from clip space to normalized device coordinates
    projected_vertex = homogeneous_to_cartesian(projected_vertex)
    x =min(IMAGE_WIDTH -1, int((projected_vertex[0] + 1) * (IMAGE_WIDTH) / 2))
    y = min(IMAGE_HEIGHT - 1, int((1 - projected_vertex[1] ) * (IMAGE_HEIGHT) / 2))
    return np.array([x, y, -projected_vertex[2]])
    return 

def edge_function(a, b, c):
    return  (b[1] - a[1]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[1] - a[1]) 


def main():
    load_obj('cow.obj')
    print("Object Loaded with vertices: ", len(vertices))
    world_to_camera = np.array([0.707107, -0.331295, 0.624695, 0, 0, 0.883452, 0.468521, 0, -0.707107, -0.331295, 0.624695, 0, -1.63871, -5.747777, -40.400412, 1])
    world_to_camera = world_to_camera.reshape((4, 4))
    projection = create_projection_matrix(FOV, 1.0, NEAR, FAR)
    for face in faces:
        triangle =[camera_to_raster(vertices[vertex], world_to_camera, projection) for vertex in face]
        print("Triangle: ", triangle)

            
            # buffer[int(vertex[1]), int(vertex[0])] = [255, 255, 255]
        min_x = min(triangle[0][0], triangle[1][0], triangle[2][0])
        max_x = max(triangle[0][0], triangle[1][0], triangle[2][0])
        min_y = min(triangle[0][1], triangle[1][1], triangle[2][1])
        max_y = max(triangle[0][1], triangle[1][1], triangle[2][1])
        # if min_x > IMAGE_WIDTH or max_x <0 or min_y > IMAGE_HEIGHT -1 or max_y < 0:
        #     print("Triangle is out of bounds")
        #     continue
        print("Triangle Transformed: ", triangle)
        x0 = max(0, min_x)
        x1 = min(IMAGE_WIDTH - 1, max_x)
        y0 = max(0, min_y)
        y1 = min(IMAGE_HEIGHT - 1, max_y)
        area = edge_function(triangle[0], triangle[1], triangle[2])
        for i in range(int(x0), int(x1) + 1):
            for j in range(int(y0), int(y1) + 1):
                p = np.array([i + 0.5, j + 0.5])
                w0 = edge_function(triangle[1], triangle[2], p)
                w1 = edge_function(triangle[2], triangle[0], p)
                w2 = edge_function(triangle[0], triangle[1], p)
                print("W0: ", w0)
                print("W1: ", w1)
                print("W2: ", w2)
                if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                    w0 /= area
                    w1 /= area
                    w2 /= area
                    z = 1 / (w0 * triangle[0][2] + w1 * triangle[1][2] + w2 * triangle[2][2])
                    # print("Z: ", z)
                    # print("Depth Buffer: ", depth_buffer[j, i])
                    if z < depth_buffer[j, i]:
                        print("Updating Depth Buffer")
                        print("J: ", j)
                        print("I: ", i)
                        depth_buffer[j, i] = z
                        buffer[j, i] = [255, 255, 255]
    image = Image.fromarray(buffer)
    image.show()

    


if __name__=="__main__":
    main()