“””
Analyze Skeleton - Python implementation
Based on ImageJ’s AnalyzeSkeleton plugin by Ignacio Arganda-Carreras

This implementation analyzes 2D/3D skeleton images and extracts:

- Branches (edges connecting endpoints/junctions)
- Endpoints (pixels with <2 neighbors)
- Junctions (pixels with >2 neighbors)
- Branch lengths and statistics

References:

- Original ImageJ plugin: https://github.com/fiji/AnalyzeSkeleton
- Paper: Arganda-Carreras et al., Microscopy Research and Technique, 2010
  “””

import numpy as np
from scipy import ndimage
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional

@dataclass
class Point:
“”“Represents a point in 2D or 3D space”””
x: int
y: int
z: int = 0

```
def __hash__(self):
    return hash((self.x, self.y, self.z))

def __eq__(self, other):
    return (self.x, self.y, self.z) == (other.x, other.y, other.z)
```

@dataclass
class Branch:
“”“Represents a branch (edge) in the skeleton”””
points: List[Point]
v1: Optional[‘Vertex’] = None  # Start vertex
v2: Optional[‘Vertex’] = None  # End vertex
length: float = 0.0
euclidean_distance: float = 0.0

```
def calculate_length(self, pixel_size=(1.0, 1.0, 1.0)):
    """Calculate the length of the branch"""
    if len(self.points) < 2:
        self.length = 0.0
        return
    
    total_length = 0.0
    for i in range(len(self.points) - 1):
        p1, p2 = self.points[i], self.points[i + 1]
        dx = (p2.x - p1.x) * pixel_size[0]
        dy = (p2.y - p1.y) * pixel_size[1]
        dz = (p2.z - p1.z) * pixel_size[2]
        total_length += np.sqrt(dx**2 + dy**2 + dz**2)
    
    self.length = total_length
    
    # Calculate Euclidean distance between endpoints
    if len(self.points) >= 2:
        p1, p2 = self.points[0], self.points[-1]
        dx = (p2.x - p1.x) * pixel_size[0]
        dy = (p2.y - p1.y) * pixel_size[1]
        dz = (p2.z - p1.z) * pixel_size[2]
        self.euclidean_distance = np.sqrt(dx**2 + dy**2 + dz**2)
```

@dataclass
class Vertex:
“”“Represents a vertex (junction or endpoint) in the skeleton”””
points: List[Point]
branches: List[Branch]
vertex_type: str  # ‘endpoint’, ‘junction’

@dataclass
class SkeletonResult:
“”“Results from skeleton analysis”””
num_branches: int = 0
num_endpoints: int = 0
num_junctions: int = 0
num_triple_points: int = 0
num_quadruple_points: int = 0
average_branch_length: float = 0.0
max_branch_length: float = 0.0
branches: List[Branch] = None
vertices: List[Vertex] = None

```
def __post_init__(self):
    if self.branches is None:
        self.branches = []
    if self.vertices is None:
        self.vertices = []
```

class AnalyzeSkeleton:
“””
Analyzes 2D/3D skeleton images
“””

```
# Voxel type constants
ENDPOINT = 30
JUNCTION = 70
SLAB = 127

def __init__(self):
    self.input_image = None
    self.tagged_image = None
    self.width = 0
    self.height = 0
    self.depth = 0
    self.pixel_size = (1.0, 1.0, 1.0)
    
def setup(self, image: np.ndarray, pixel_size=(1.0, 1.0, 1.0)):
    """
    Setup the analyzer with an input image
    
    Args:
        image: Binary skeleton image (2D or 3D numpy array)
        pixel_size: Tuple of (x, y, z) pixel sizes for calibration
    """
    self.input_image = image.astype(np.uint8)
    self.pixel_size = pixel_size
    
    if image.ndim == 2:
        self.height, self.width = image.shape
        self.depth = 1
        self.input_image = image[np.newaxis, :, :]
    elif image.ndim == 3:
        self.depth, self.height, self.width = image.shape
    else:
        raise ValueError("Input image must be 2D or 3D")
        
    self.tagged_image = np.zeros_like(self.input_image, dtype=np.uint8)

def get_neighbors_26(self, x: int, y: int, z: int) -> List[Point]:
    """Get 26-connected neighbors in 3D (or 8-connected in 2D)"""
    neighbors = []
    for dz in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                nx, ny, nz = x + dx, y + dy, z + dz
                if (0 <= nx < self.width and 
                    0 <= ny < self.height and 
                    0 <= nz < self.depth):
                    if self.input_image[nz, ny, nx] > 0:
                        neighbors.append(Point(nx, ny, nz))
    return neighbors

def classify_voxel(self, x: int, y: int, z: int) -> int:
    """
    Classify a voxel as endpoint, junction, or slab based on neighbors
    
    Returns:
        ENDPOINT (< 2 neighbors), JUNCTION (> 2 neighbors), or SLAB (2 neighbors)
    """
    neighbors = self.get_neighbors_26(x, y, z)
    n_neighbors = len(neighbors)
    
    if n_neighbors < 2:
        return self.ENDPOINT
    elif n_neighbors > 2:
        return self.JUNCTION
    else:
        return self.SLAB

def tag_skeleton(self):
    """Tag all pixels in the skeleton image"""
    for z in range(self.depth):
        for y in range(self.height):
            for x in range(self.width):
                if self.input_image[z, y, x] > 0:
                    voxel_type = self.classify_voxel(x, y, z)
                    self.tagged_image[z, y, x] = voxel_type

def find_vertices(self) -> List[Vertex]:
    """Find all endpoints and junctions"""
    vertices = []
    visited = set()
    
    # Find all endpoints and junction points
    for z in range(self.depth):
        for y in range(self.height):
            for x in range(self.width):
                voxel_type = self.tagged_image[z, y, x]
                
                if voxel_type in (self.ENDPOINT, self.JUNCTION):
                    point = Point(x, y, z)
                    if point not in visited:
                        # Group neighboring junction voxels together
                        vertex_points = [point]
                        visited.add(point)
                        
                        if voxel_type == self.JUNCTION:
                            # Find connected junction voxels
                            queue = deque([point])
                            while queue:
                                p = queue.popleft()
                                neighbors = self.get_neighbors_26(p.x, p.y, p.z)
                                for n in neighbors:
                                    if (self.tagged_image[n.z, n.y, n.x] == self.JUNCTION and
                                        n not in visited):
                                        vertex_points.append(n)
                                        visited.add(n)
                                        queue.append(n)
                        
                        vertex_type = 'junction' if voxel_type == self.JUNCTION else 'endpoint'
                        vertices.append(Vertex(vertex_points, [], vertex_type))
    
    return vertices

def trace_branch(self, start: Point, prev: Point, vertices_dict: Dict) -> Branch:
    """
    Trace a branch from a starting point until reaching another vertex
    
    Args:
        start: Starting point
        prev: Previous point (to avoid backtracking)
        vertices_dict: Dictionary mapping points to vertices
    """
    branch_points = [start]
    current = start
    previous = prev
    
    while True:
        # Get neighbors
        neighbors = self.get_neighbors_26(current.x, current.y, current.z)
        
        # Find next point (not the previous one)
        next_points = [n for n in neighbors if n != previous]
        
        if not next_points:
            break
        
        # If we hit a vertex, stop
        if len(next_points) > 1 or next_points[0] in vertices_dict:
            if next_points[0] not in branch_points:
                branch_points.append(next_points[0])
            break
        
        # Continue along the branch
        previous = current
        current = next_points[0]
        branch_points.append(current)
        
        # Safety check for loops
        if len(branch_points) > self.width * self.height * self.depth:
            break
    
    branch = Branch(branch_points)
    branch.calculate_length(self.pixel_size)
    return branch

def find_branches(self, vertices: List[Vertex]) -> List[Branch]:
    """Find all branches connecting vertices"""
    branches = []
    
    # Create a dictionary for quick vertex lookup
    vertices_dict = {}
    for vertex in vertices:
        for point in vertex.points:
            vertices_dict[point] = vertex
    
    # Trace branches from each vertex
    visited_pairs = set()
    
    for vertex in vertices:
        for start_point in vertex.points:
            neighbors = self.get_neighbors_26(start_point.x, start_point.y, start_point.z)
            
            for neighbor in neighbors:
                # Skip if this is another point in the same vertex
                if neighbor in vertex.points:
                    continue
                
                # Create a unique identifier for this vertex pair
                pair_id = (id(vertex), neighbor.x, neighbor.y, neighbor.z)
                if pair_id in visited_pairs:
                    continue
                visited_pairs.add(pair_id)
                
                # Trace the branch
                branch = self.trace_branch(neighbor, start_point, vertices_dict)
                
                if len(branch.points) > 0:
                    branch.v1 = vertex
                    
                    # Find ending vertex
                    end_point = branch.points[-1]
                    if end_point in vertices_dict:
                        branch.v2 = vertices_dict[end_point]
                    
                    branches.append(branch)
                    vertex.branches.append(branch)
    
    return branches

def run(self, verbose=True) -> SkeletonResult:
    """
    Run the skeleton analysis
    
    Args:
        verbose: Print progress information
        
    Returns:
        SkeletonResult object with analysis results
    """
    if self.input_image is None:
        raise ValueError("No image loaded. Call setup() first.")
    
    if verbose:
        print("Tagging skeleton...")
    self.tag_skeleton()
    
    if verbose:
        print("Finding vertices...")
    vertices = self.find_vertices()
    
    if verbose:
        print("Tracing branches...")
    branches = self.find_branches(vertices)
    
    # Calculate statistics
    result = SkeletonResult()
    result.branches = branches
    result.vertices = vertices
    result.num_branches = len(branches)
    
    # Count endpoints and junctions
    for vertex in vertices:
        if vertex.vertex_type == 'endpoint':
            result.num_endpoints += 1
        else:
            result.num_junctions += 1
            n_branches = len(vertex.branches)
            if n_branches == 3:
                result.num_triple_points += 1
            elif n_branches == 4:
                result.num_quadruple_points += 1
    
    # Branch length statistics
    if branches:
        branch_lengths = [b.length for b in branches]
        result.average_branch_length = np.mean(branch_lengths)
        result.max_branch_length = np.max(branch_lengths)
    
    if verbose:
        print(f"\nResults:")
        print(f"  Branches: {result.num_branches}")
        print(f"  Endpoints: {result.num_endpoints}")
        print(f"  Junctions: {result.num_junctions}")
        print(f"  Triple points: {result.num_triple_points}")
        print(f"  Quadruple points: {result.num_quadruple_points}")
        if branches:
            print(f"  Average branch length: {result.average_branch_length:.2f}")
            print(f"  Max branch length: {result.max_branch_length:.2f}")
    
    return result

def get_tagged_image(self) -> np.ndarray:
    """Get the tagged image showing voxel types"""
    if self.depth == 1:
        return self.tagged_image[0]
    return self.tagged_image
```

# Example usage

if **name** == “**main**”:
# Create a simple test skeleton
skeleton = np.zeros((50, 50), dtype=np.uint8)

```
# Draw a Y-shape
skeleton[10:30, 25] = 255  # Vertical line
skeleton[30, 15:26] = 255  # Left branch
skeleton[30, 25:36] = 255  # Right branch

# Analyze
analyzer = AnalyzeSkeleton()
analyzer.setup(skeleton, pixel_size=(1.0, 1.0, 1.0))
result = analyzer.run(verbose=True)

# Display tagged image
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.imshow(skeleton, cmap='gray')
ax1.set_title('Original Skeleton')
ax1.axis('off')

tagged = analyzer.get_tagged_image()
ax2.imshow(tagged, cmap='jet')
ax2.set_title('Tagged Skeleton\n(Blue=Endpoint, Red=Junction, Orange=Slab)')
ax2.axis('off')

plt.tight_layout()
plt.show()

# Print branch details
print("\nBranch details:")
for i, branch in enumerate(result.branches):
    print(f"Branch {i+1}: Length={branch.length:.2f}, "
          f"Points={len(branch.points)}, "
          f"Euclidean={branch.euclidean_distance:.2f}")
```