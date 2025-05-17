import os 
import json
import numpy as np
from PIL import Image
vertices = []
faces = []
FOV = 90
NEAR = 0.1
FAR = 100
IMAGE_WITH = 512
IMAGE_HEIGHT = 512
buffer = np.zeros((IMAGE_HEIGHT, IMAGE_WITH, 3), dtype=np.uint8)
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
                    face = [int(i.split('/')[0]) - 1 for i in face[1:]]
                    print(face)
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

    camera_space_vertex = np.matmul(vertex_homogeneous, world_to_camera)
    camera_space_vertex = homogeneous_to_cartesian(camera_space_vertex)

    projected_vertex = np.matmul(camera_space_vertex, projection)
    projected_vertex = homogeneous_to_cartesian(projected_vertex)
    if (projected_vertex[0] < -1 or projected_vertex[0] > 1 or
        projected_vertex[1] < -1 or projected_vertex[1] > 1 or
        projected_vertex[2] < NEAR or projected_vertex[2] > FAR):
        return np.inf, np.inf
    x =min(IMAGE_WITH -1, int((projected_vertex[0] + 1) * (IMAGE_WITH) / 2))
    y = min(IMAGE_HEIGHT - 1, int((1 - projected_vertex[1] ) * (IMAGE_HEIGHT) / 2))
    return x, y

def edge_function(x0, y0, x1, y1):
    return (x1 - x0) * (y0 - y1) - (x0 - x1) * (y1 - y0)

def main():
    load_obj('cow.obj')
    print("Object Loaded with vertices: ", len(vertices))
    world_to_camera = np.eye(4)
    world_to_camera[3, 2] = -20 
    world_to_camera[3, 1] = -10
    world_to_camera[2, 3] = -100
    projection = create_projection_matrix(FOV, 1.0, NEAR, FAR)
    for face in faces:
        triangle = [vertices[vertex] for vertex in face]
        for vertex in triangle:
            x, y = camera_to_raster(vertex, world_to_camera, projection)
            if x != np.inf and y != np.inf:
                buffer[y, x] = [255, 255, 255]
    image = Image.fromarray(buffer)
    image.show()

    


if __name__=="__main__":
    main()