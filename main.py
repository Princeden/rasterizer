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
    # convert from world space to camera space
    camera_space_vertex = np.matmul(vertex_homogeneous, world_to_camera)
    camera_space_vertex = homogeneous_to_cartesian(camera_space_vertex)
    # project from camera space to clip space
    projected_vertex = np.matmul(camera_space_vertex, projection)
    # convert from clip space to normalized device coordinates
    projected_vertex = homogeneous_to_cartesian(projected_vertex)
    # check if the vertex is in the view frustum
    if (projected_vertex[0] < -1 or projected_vertex[0] > 1 or
        projected_vertex[1] < -1 or projected_vertex[1] > 1 or
        projected_vertex[2] < NEAR or projected_vertex[2] > FAR):
        return np.inf, np.inf
    # convert from normalized device coordinates to raster space
    x =min(IMAGE_WIDTH -1, int((projected_vertex[0] + 1) * (IMAGE_WIDTH) / 2))
    y = min(IMAGE_HEIGHT - 1, int((1 - projected_vertex[1] ) * (IMAGE_HEIGHT) / 2))
    return x, y

def edge_function(a, b,c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    

def main():
    load_obj('cow.obj')
    print("Object Loaded with vertices: ", len(vertices))
    world_to_camera = np.eye(4)
    world_to_camera[3, 2] = -20 
    world_to_camera[3, 1] = -10
    world_to_camera[2, 3] = -100
    projection = create_projection_matrix(FOV, 1.0, NEAR, FAR)
    depth_buffer = np.full((IMAGE_HEIGHT, IMAGE_WIDTH), np.inf)
    for i in range(len(faces)):
        face = faces
        triangle = [camera_to_raster(vertices[vertex], world_to_camera,projection) for vertex in face]
        
        xmax = max(triangle[0][0], triangle[1][0], triangle[2][0], IMAGE_WIDTH - 1)
        xmin = min(triangle[0][0], triangle[1][0], triangle[2][0], 0)
        ymax = max(triangle[0][1], triangle[1][1], triangle[2][1], IMAGE_HEIGHT - 1)
        ymin = min(triangle[0][1], triangle[1][1], triangle[2][1], 0)
        for y in range(ymin, ymax + 1):
            for x in range(xmin, xmax + 1):
        
                area = edge_function(triangle[0], triangle[1], triangle[2]) 
                pixel = np.array([x+ 0.5, y+0.5, 0])
                w0 = edge_function(triangle[0], triangle[1], pixel)
                w1 = edge_function(triangle[1], triangle[2], pixel)
                w2 = edge_function(triangle[2], triangle[0], pixel)
                # check if the pixel is inside the triangle
                if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                    # compute the barycentric coordinates
                    w0 = w0 / area
                    w1 = w1 / area  
                    w2 = w2 / area
                    z = 1 / (triangle[0][2] * w0 + triangle[1][2] * w1 + triangle[2][2] * w2) 
                    # texture_vector = textures[i]
                    # texture_vector = map(lambda n: n * z, texture_vector)
                    # texture = texture_vector[0] * w0 + texture_vector[1] * w1 + texture_vector[2] * w2
                    if depth_buffer[y, x] > z:
                        depth_buffer[y, x] = z
                        buffer[y, x] = [255, 255, 255]
                    
    image = Image.fromarray(buffer)
    image.show()

    


if __name__=="__main__":
    main()