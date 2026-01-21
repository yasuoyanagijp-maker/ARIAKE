“””
スケルトン解析モジュール
ImageJのAnalyze Skeletonプラグインの実装を統合
血管のスケルトン化、径測定、分岐点解析、トルトゥオシティ計算
“””
import numpy as np
import cv2
from scipy import ndimage
from skimage import morphology, measure
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from collections import deque
import warnings

warnings.filterwarnings(‘ignore’)

@dataclass
class Point:
“”“スケルトン上の点を表現”””
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
“”“ブランチ（エッジ）を表現”””
points: List[Point]
v1: Optional[‘Vertex’] = None  # 始点
v2: Optional[‘Vertex’] = None  # 終点
length: float = 0.0
euclidean_distance: float = 0.0

```
def calculate_length(self, pixel_size=(1.0, 1.0, 1.0)):
    """ブランチの長さを計算"""
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
    
    # ユークリッド距離を計算
    if len(self.points) >= 2:
        p1, p2 = self.points[0], self.points[-1]
        dx = (p2.x - p1.x) * pixel_size[0]
        dy = (p2.y - p1.y) * pixel_size[1]
        dz = (p2.z - p1.z) * pixel_size[2]
        self.euclidean_distance = np.sqrt(dx**2 + dy**2 + dz**2)
```

@dataclass
class Vertex:
“”“頂点（分岐点または端点）を表現”””
points: List[Point]
branches: List[Branch]
vertex_type: str  # ‘endpoint’, ‘junction’

class SkeletonAnalyzer:
“””
ImageJのAnalyze Skeletonプラグインを模倣したスケルトン解析
performSkeletonAnalysisImproved に対応
“””

```
# ボクセルタイプの定数
ENDPOINT = 30
JUNCTION = 70
SLAB = 127

def __init__(self, mm_per_pixel: float):
    """
    Parameters:
    -----------
    mm_per_pixel : float
        ピクセルあたりのmm
    """
    self.mm_per_pixel = mm_per_pixel
    self.pixel_size_um = mm_per_pixel * 1000
    
    # ImageJ Analyze Skeleton用
    self.input_image = None
    self.tagged_image = None
    self.width = 0
    self.height = 0
    self.depth = 0

def skeletonize(self, binary: np.ndarray) -> np.ndarray:
    """
    スケルトン化
    
    Parameters:
    -----------
    binary : np.ndarray
        二値画像
        
    Returns:
    --------
    skeleton : np.ndarray
        スケルトン画像
    """
    skeleton_bool = morphology.skeletonize(binary > 0)
    skeleton = (skeleton_bool * 255).astype(np.uint8)
    return skeleton

def setup_imagej_analyzer(self, skeleton: np.ndarray):
    """ImageJ Analyze Skeletonの初期化"""
    self.input_image = skeleton.astype(np.uint8)
    
    if skeleton.ndim == 2:
        self.height, self.width = skeleton.shape
        self.depth = 1
        self.input_image = skeleton[np.newaxis, :, :]
    elif skeleton.ndim == 3:
        self.depth, self.height, self.width = skeleton.shape
    else:
        raise ValueError("Input image must be 2D or 3D")
        
    self.tagged_image = np.zeros_like(self.input_image, dtype=np.uint8)

def get_neighbors_26(self, x: int, y: int, z: int) -> List[Point]:
    """26連結近傍を取得（2Dの場合は8連結）"""
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
    ボクセルを端点・分岐点・通常点に分類
    
    Returns:
        ENDPOINT (<2 neighbors), JUNCTION (>2 neighbors), SLAB (2 neighbors)
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
    """スケルトン内の全ピクセルをタグ付け"""
    for z in range(self.depth):
        for y in range(self.height):
            for x in range(self.width):
                if self.input_image[z, y, x] > 0:
                    voxel_type = self.classify_voxel(x, y, z)
                    self.tagged_image[z, y, x] = voxel_type

def find_vertices(self) -> List[Vertex]:
    """全ての端点と分岐点を検出"""
    vertices = []
    visited = set()
    
    for z in range(self.depth):
        for y in range(self.height):
            for x in range(self.width):
                voxel_type = self.tagged_image[z, y, x]
                
                if voxel_type in (self.ENDPOINT, self.JUNCTION):
                    point = Point(x, y, z)
                    if point not in visited:
                        vertex_points = [point]
                        visited.add(point)
                        
                        if voxel_type == self.JUNCTION:
                            # 連結した分岐点をグループ化
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
    ブランチをトレース
    
    Parameters:
        start: 開始点
        prev: 前の点（逆方向を防ぐ）
        vertices_dict: 点から頂点へのマッピング
    """
    branch_points = [start]
    current = start
    previous = prev
    
    while True:
        neighbors = self.get_neighbors_26(current.x, current.y, current.z)
        next_points = [n for n in neighbors if n != previous]
        
        if not next_points:
            break
        
        # 頂点に到達したら停止
        if len(next_points) > 1 or next_points[0] in vertices_dict:
            if next_points[0] not in branch_points:
                branch_points.append(next_points[0])
            break
        
        # ブランチに沿って続ける
        previous = current
        current = next_points[0]
        branch_points.append(current)
        
        # ループ検出
        if len(branch_points) > self.width * self.height * self.depth:
            break
    
    branch = Branch(branch_points)
    pixel_size = (self.mm_per_pixel, self.mm_per_pixel, self.mm_per_pixel)
    branch.calculate_length(pixel_size)
    return branch

def find_branches(self, vertices: List[Vertex]) -> List[Branch]:
    """頂点を接続する全てのブランチを検出"""
    branches = []
    
    vertices_dict = {}
    for vertex in vertices:
        for point in vertex.points:
            vertices_dict[point] = vertex
    
    visited_pairs = set()
    
    for vertex in vertices:
        for start_point in vertex.points:
            neighbors = self.get_neighbors_26(start_point.x, start_point.y, start_point.z)
            
            for neighbor in neighbors:
                if neighbor in vertex.points:
                    continue
                
                pair_id = (id(vertex), neighbor.x, neighbor.y, neighbor.z)
                if pair_id in visited_pairs:
                    continue
                visited_pairs.add(pair_id)
                
                branch = self.trace_branch(neighbor, start_point, vertices_dict)
                
                if len(branch.points) > 0:
                    branch.v1 = vertex
                    
                    end_point = branch.points[-1]
                    if end_point in vertices_dict:
                        branch.v2 = vertices_dict[end_point]
                    
                    branches.append(branch)
                    vertex.branches.append(branch)
    
    return branches

def analyze_skeleton_structure(self, skeleton: np.ndarray) -> Dict[str, any]:
    """
    スケルトンの構造解析（ImageJ Analyze Skeleton互換）
    
    Parameters:
    -----------
    skeleton : np.ndarray
        スケルトン画像
        
    Returns:
    --------
    results : dict
        解析結果
    """
    # ImageJ Analyze Skeletonの実行
    self.setup_imagej_analyzer(skeleton)
    self.tag_skeleton()
    
    vertices = self.find_vertices()
    branches = self.find_branches(vertices)
    
    # 端点と分岐点のカウント
    num_endpoints = sum(1 for v in vertices if v.vertex_type == 'endpoint')
    num_junctions = sum(1 for v in vertices if v.vertex_type == 'junction')
    
    # トリプル・クアドラプルポイント
    num_triple = 0
    num_quadruple = 0
    for vertex in vertices:
        if vertex.vertex_type == 'junction':
            n_branches = len(vertex.branches)
            if n_branches == 3:
                num_triple += 1
            elif n_branches == 4:
                num_quadruple += 1
    
    # ブランチ長の情報
    branch_lengths = [b.length for b in branches]
    branch_euclidean_distances = [b.euclidean_distance for b in branches]
    
    # 端点・分岐点の座標
    endpoint_positions = []
    junction_positions = []
    for vertex in vertices:
        if vertex.points:
            p = vertex.points[0]
            if vertex.vertex_type == 'endpoint':
                endpoint_positions.append((p.x, p.y))
            else:
                junction_positions.append((p.x, p.y))
    
    # 連結成分数
    if skeleton.ndim == 2:
        num_labels = cv2.connectedComponents(skeleton, connectivity=8)[0]
    else:
        num_labels = cv2.connectedComponents(skeleton[0], connectivity=8)[0]
    
    results = {
        'num_branches': len(branches),
        'num_junctions': num_junctions,
        'num_endpoints': num_endpoints,
        'num_triple_points': num_triple,
        'num_quadruple_points': num_quadruple,
        'num_skeletons': num_labels - 1,
        'branch_lengths': branch_lengths,
        'branch_euclidean_distances': branch_euclidean_distances,
        'junction_positions': junction_positions,
        'endpoint_positions': endpoint_positions,
        'branches': branches,
        'vertices': vertices
    }
    
    return results
```

class DiameterAnalyzer:
“””
血管径解析クラス
performVesselDiameterAnalysis に対応
“””

```
def __init__(self, mm_per_pixel: float):
    """
    Parameters:
    -----------
    mm_per_pixel : float
        ピクセルあたりのmm
    """
    self.mm_per_pixel = mm_per_pixel
    self.pixel_size_um = mm_per_pixel * 1000

def create_distance_map(self, binary: np.ndarray) -> np.ndarray:
    """
    距離マップを作成
    
    Parameters:
    -----------
    binary : np.ndarray
        二値画像
        
    Returns:
    --------
    distance_map : np.ndarray
        距離マップ（各ピクセルから最近傍の背景までの距離）
    """
    distance_map = cv2.distanceTransform(
        binary,
        cv2.DIST_L2,
        cv2.DIST_MASK_PRECISE
    )
    
    return distance_map

def analyze_diameter_statistics(self,
                                distance_map: np.ndarray,
                                skeleton: np.ndarray) -> Dict[str, float]:
    """
    径の統計量を計算
    
    Parameters:
    -----------
    distance_map : np.ndarray
        距離マップ
    skeleton : np.ndarray
        スケルトン画像
        
    Returns:
    --------
    stats : dict
        統計量（単位: μm）
    """
    skeleton_mask = skeleton > 0
    skeleton_distances = distance_map[skeleton_mask]
    
    skeleton_distances = skeleton_distances[~np.isnan(skeleton_distances)]
    
    if len(skeleton_distances) == 0:
        return {
            'mean_diameter_um': 0,
            'std_diameter_um': 0,
            'max_diameter_um': 0,
            'max_mean_ratio': 0,
            'max_mean_sd': 0,
            'cv_diameter': 0
        }
    
    mean_dist = skeleton_distances.mean()
    std_dist = skeleton_distances.std()
    max_dist = skeleton_distances.max()
    
    mean_diameter_um = mean_dist * 2 * self.pixel_size_um
    std_diameter_um = std_dist * 2 * self.pixel_size_um
    max_diameter_um = max_dist * 2 * self.pixel_size_um
    
    if std_dist > 0:
        max_mean_ratio = (max_dist - mean_dist) / std_dist
    else:
        max_mean_ratio = 0
    
    if max_dist > 0:
        max_mean_sd = 100 * std_dist / max_dist
    else:
        max_mean_sd = 0
    
    if mean_diameter_um > 0:
        cv_diameter = 100 * std_diameter_um / mean_diameter_um
    else:
        cv_diameter = 0
    
    stats = {
        'mean_diameter_um': mean_diameter_um,
        'std_diameter_um': std_diameter_um,
        'max_diameter_um': max_diameter_um,
        'max_mean_ratio': max_mean_ratio,
        'max_mean_sd': max_mean_sd,
        'cv_diameter': cv_diameter
    }
    
    return stats
```

class BranchAnalyzer:
“””
ブランチ情報解析クラス
processBranchInformation に対応
“””

```
def __init__(self, mm_per_pixel: float, skeleton_diameter_um: float):
    """
    Parameters:
    -----------
    mm_per_pixel : float
        ピクセルあたりのmm
    skeleton_diameter_um : float
        平均血管径（μm）
    """
    self.mm_per_pixel = mm_per_pixel
    self.skeleton_diameter_um = skeleton_diameter_um

def calculate_tortuosity(self,
                        branch_lengths: List[float],
                        euclidean_distances: List[float]) -> Tuple[float, float]:
    """
    トルトゥオシティ（屈曲度）を計算
    
    Parameters:
    -----------
    branch_lengths : list of float
        ブランチ長のリスト（ピクセル）
    euclidean_distances : list of float
        ユークリッド距離のリスト（ピクセル）
        
    Returns:
    --------
    mean_tortuosity : float
        平均トルトゥオシティ
    total_length_mm : float
        総血管長（mm）
    """
    threshold_mm = self.skeleton_diameter_um / 1000.0
    threshold_pixels = threshold_mm / self.mm_per_pixel
    
    sum_weighted_tortuosity = 0.0
    sum_filtered_length = 0.0
    total_length = 0.0
    
    for length, euc_dist in zip(branch_lengths, euclidean_distances):
        total_length += length
        
        if euc_dist > threshold_pixels and euc_dist > 0:
            tortuosity = length / euc_dist
            
            if 1.0 <= tortuosity < 10.0:
                sum_weighted_tortuosity += length * tortuosity
                sum_filtered_length += length
    
    if sum_filtered_length > 0:
        mean_tortuosity = sum_weighted_tortuosity / sum_filtered_length
    else:
        mean_tortuosity = 0.0
    
    if np.isnan(mean_tortuosity) or mean_tortuosity > 1000:
        mean_tortuosity = 0.0
    
    total_length_mm = total_length * self.mm_per_pixel
    
    return mean_tortuosity, total_length_mm

def calculate_corrected_values(self,
                              vessel_length_mm: float,
                              vessel_area_mm2: float,
                              triple_points: int,
                              quadruple_points: int) -> Tuple[float, float]:
    """
    補正された血管径と血管長を計算
    calculateCorrectedValues に対応
    
    Parameters:
    -----------
    vessel_length_mm : float
        血管長（mm）
    vessel_area_mm2 : float
        血管面積（mm²）
    triple_points : int
        3分岐点の数
    quadruple_points : int
        4分岐点の数
        
    Returns:
    --------
    corrected_diameter_um : float
        補正血管径（μm）
    corrected_length_mm : float
        補正血管長（mm）
    """
    if vessel_length_mm > 0 and (triple_points > 0 or quadruple_points > 0):
        discriminant = (vessel_length_mm ** 2 - 
                      4 * (triple_points / 2 + quadruple_points) * vessel_area_mm2)
        
        if discriminant >= 0:
            corrected_diameter_um = 1000 * (
                vessel_length_mm - np.sqrt(discriminant)
            ) / (2 * (triple_points / 2 + quadruple_points))
        else:
            corrected_diameter_um = 1000 * (vessel_area_mm2 / vessel_length_mm)
        
        corrected_length_mm = (vessel_length_mm - 
                              triple_points * self.skeleton_diameter_um / 2000 -
                              quadruple_points * self.skeleton_diameter_um / 1000)
        corrected_length_mm = max(corrected_length_mm, 0)
    else:
        if vessel_length_mm > 0:
            corrected_diameter_um = 1000 * (vessel_area_mm2 / vessel_length_mm)
        else:
            corrected_diameter_um = 0
        corrected_length_mm = vessel_length_mm
    
    return corrected_diameter_um, corrected_length_mm

def calculate_densities(self,
                      vessel_length_mm: float,
                      num_branches: int,
                      num_junctions: int,
                      num_endpoints: int,
                      num_triple: int,
                      num_quadruple: int) -> Dict[str, float]:
    """
    各種密度を計算
    
    Parameters:
    -----------
    vessel_length_mm : float
        血管長（mm）
    num_branches : int
        ブランチ数
    num_junctions : int
        分岐点数
    num_endpoints : int
        端点数
    num_triple : int
        3分岐点数
    num_quadruple : int
        4分岐点数
        
    Returns:
    --------
    densities : dict
        各種密度（単位: /mm）
    """
    if vessel_length_mm > 0:
        branch_density = num_branches / vessel_length_mm
        junction_density = num_junctions / vessel_length_mm
        endpoint_density = num_endpoints / vessel_length_mm
        multiple_density = (num_triple + num_quadruple) / vessel_length_mm
    else:
        branch_density = 0
        junction_density = 0
        endpoint_density = 0
        multiple_density = 0
    
    return {
        'branch_density': branch_density,
        'junction_density': junction_density,
        'endpoint_density': endpoint_density,
        'multiple_density': multiple_density
    }
```

class TaggedSkeletonProcessor:
“””
Tagged Skeletonの処理
processTaggedSkeleton, createRefinedSkeleton に対応
“””

```
@staticmethod
def create_tagged_skeleton(skeleton: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Tagged Skeletonを作成
    
    Parameters:
    -----------
    skeleton : np.ndarray
        スケルトン画像
        
    Returns:
    --------
    tagged : dict
        'red': ブランチ（通常の骨格点）
        'blue': 分岐点
        'green': 端点
    """
    kernel = np.array([[1, 1, 1],
                      [1, 10, 1],
                      [1, 1, 1]], dtype=np.uint8)
    
    filtered = cv2.filter2D(skeleton // 255, -1, kernel)
    
    junctions_mask = (filtered >= 13) & (skeleton > 0)
    endpoints_mask = (filtered == 11) & (skeleton > 0)
    branches_mask = (skeleton > 0) & ~junctions_mask & ~endpoints_mask
    
    tagged = {
        'red': (branches_mask * 255).astype(np.uint8),
        'blue': (junctions_mask * 255).astype(np.uint8),
        'green': (endpoints_mask * 255).astype(np.uint8)
    }
    
    return tagged

@staticmethod
def apply_diameter_length_filter(red_channel: np.ndarray,
                                 distance_map: np.ndarray,
                                 threshold: float = 0.7) -> np.ndarray:
    """
    径/長さ比によるフィルタリング
    
    Parameters:
    -----------
    red_channel : np.ndarray
        Red channel（ブランチ）
    distance_map : np.ndarray
        距離マップ
    threshold : float
        閾値（径/長さ比）
        
    Returns:
    --------
    filtered : np.ndarray
        フィルタ後の画像
    """
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        red_channel, connectivity=8
    )
    
    result = np.zeros_like(red_channel)
    
    for i in range(1, num_labels):
        component_mask = (labels == i)
        component_pixels = np.sum(component_mask)
        
        if component_pixels == 0:
            continue
        
        mean_diameter = distance_map[component_mask].mean()
        ratio = mean_diameter / component_pixels
        
        if ratio > threshold:
            result[component_mask] = 255
    
    return result

@staticmethod
def remove_isolated_junctions(skeleton: np.ndarray,
                              max_area: float) -> np.ndarray:
    """
    孤立した分岐点を除去
    
    Parameters:
    -----------
    skeleton : np.ndarray
        スケルトン画像
    max_area : float
        最大面積（これより小さい成分を削除）
        
    Returns:
    --------
    cleaned : np.ndarray
        クリーニング後の画像
    """
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        skeleton, connectivity=8
    )
    
    result = np.zeros_like(skeleton)
    
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= max_area:
            result[labels == i] = 255
    
    return result

@staticmethod
def create_refined_skeleton(tagged: Dict[str, np.ndarray],
                           distance_map: np.ndarray,
                           max_junction_area: float) -> np.ndarray:
    """
    Refined Skeletonを作成
    
    Parameters:
    -----------
    tagged : dict
        Tagged skeleton（'red', 'blue'チャンネル）
    distance_map : np.ndarray
        距離マップ
    max_junction_area : float
        分岐点の最大面積
        
    Returns:
    --------
    refined : np.ndarray
        精製されたスケルトン
    """
    red = tagged['red']
    blue = tagged['blue']
    
    subtracted = cv2.subtract(red, blue)
    
    filtered = TaggedSkeletonProcessor.apply_diameter_length_filter(
        subtracted, distance_map
    )
    
    combined = cv2.add(filtered, blue)
    
    refined = TaggedSkeletonProcessor.remove_isolated_junctions(
        combined, max_junction_area
    )
    
    return refined
```

class FractalAnalyzer:
“””
フラクタル次元解析
calculateFractalDimensionBoxCounting に対応
“””

```
@staticmethod
def box_counting(binary: np.ndarray,
                min_box_size: int = 2,
                max_box_size: Optional[int] = None) -> Tuple[List[int], List[int]]:
    """
    Box-counting法によるフラクタル次元計算の準備
    
    Parameters:
    -----------
    binary : np.ndarray
        二値画像
    min_box_size : int
        最小ボックスサイズ
    max_box_size : int, optional
        最大ボックスサイズ
        
    Returns:
    --------
    box_sizes : list of int
        ボックスサイズのリスト
    box_counts : list of int
        各サイズでのボックス数
    """
    h, w = binary.shape
    max_dim = max(h, w)
    
    if max_box_size is None:
        max_box_size = 2 ** int(np.log2(max_dim / 4))
    
    box_sizes = []
    box_counts = []
    
    box_size = min_box_size
    while box_size <= max_box_size:
        count = FractalAnalyzer._count_boxes(binary, box_size)
        
        if count > 0:
            box_sizes.append(box_size)
            box_counts.append(count)
        
        box_size *= 2
    
    return box_sizes, box_counts

@staticmethod
def _count_boxes(binary: np.ndarray, box_size: int) -> int:
    """
    指定サイズのボックスでスケルトンを含むボックスをカウント
    """
    h, w = binary.shape
    count = 0
    
    for y in range(0, h, box_size):
        for x in range(0, w, box_size):
            y_end = min(y + box_size, h)
            x_end = min(x + box_size, w)
            
            box_region = binary[y:y_end, x:x_end]
            
            if np.any(box_region > 0):
                count += 1
    
    return count

@staticmethod
def calculate_fractal_dimension(box_sizes: List[int],
                                box_counts: List[int]) -> Tuple[float, float]:
    """
    フラクタル次元を計算
    
    Parameters:
    -----------
    box_sizes : list of int
        ボックスサイズ
    box_counts : list of int
        ボックス数
        
    Returns:
    --------
    fractal_dimension : float
        フラクタル次元
    r_squared : float
        決定係数
    """
    if len(box_sizes) < 3:
        return 0.0, 0.0
    
    log_sizes = np.log(1.0 / np.array(box_sizes))
    log_counts = np.log(np.array(box_counts))
    
    n = len(log_sizes)
    sum_x = np.sum(log_sizes)
    sum_y = np.sum(log_counts)
    sum_xy = np.sum(log_sizes * log_counts)
    sum_x2 = np.sum(log_sizes ** 2)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    
    mean_y = sum_y / n
    ss_total = np.sum((log_counts - mean_y) ** 2)
    
    intercept = (sum_y - slope * sum_x) / n
    predicted = slope * log_sizes + intercept
    ss_residual = np.sum((log_counts - predicted) ** 2)
    
    r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
    
    if slope < 0.5 or slope > 2.5:
        return 0.0, r_squared
    
    return slope, r_squared
```

# 使用例

if **name** == “**main**”:
# サンプル画像の作成
skeleton = np.zeros((100, 100), dtype=np.uint8)

```
# Y字型のスケルトンを描画
skeleton[20:50, 50] = 255  # 垂直線
skeleton[50, 30:51] = 255  # 左枝
skeleton[50, 50:71] = 255  # 右枝

# 解析の実行
mm_per_pixel = 0.01
analyzer = SkeletonAnalyzer(mm_per_pixel)

# ImageJ Analyze Skeleton互換の解析
result = analyzer.analyze_skeleton_structure(skeleton)

print("=== スケルトン解析結果 ===")
print(f"ブランチ数: {result['num_branches']}")
print(f"端点数: {result['num_endpoints']}")
print(f"分岐点数: {result['num_junctions']}")
print(f"トリプルポイント: {result['num_triple_points']}")
print(f"クアドラプルポイント: {result['num_quadruple_points']}")

if result['branch_lengths']:
    print(f"\nブランチ長:")
    print(f"  平均: {np.mean(result['branch_lengths']):.2f} mm")
    print(f"  最大: {np.max(result['branch_lengths']):.2f} mm")
```