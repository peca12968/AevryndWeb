"""在既有角色 GLB 上建立與同一骨架綁定的合身長褲。"""

from __future__ import annotations

import argparse
import json
import math
import struct
from collections import defaultdict
from pathlib import Path


GLB_MAGIC = 0x46546C67
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def align_four(data: bytearray, fill: int = 0) -> None:
    while len(data) % 4:
        data.append(fill)


def read_glb(path: Path) -> tuple[dict, bytearray]:
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<III", data, 0)
    if (magic, version, total) != (GLB_MAGIC, 2, len(data)):
        raise ValueError("invalid_glb_header")
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != JSON_CHUNK:
        raise ValueError("missing_json_chunk")
    document = json.loads(data[20 : 20 + json_length].decode("utf-8").rstrip(" \0"))
    bin_header = 20 + json_length
    bin_length, bin_type = struct.unpack_from("<II", data, bin_header)
    if bin_type != BIN_CHUNK:
        raise ValueError("missing_bin_chunk")
    binary = bytearray(data[bin_header + 8 : bin_header + 8 + bin_length])
    return document, binary


def decode_accessor(document: dict, binary: bytearray, index: int) -> list[tuple[float, ...]]:
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    code = {5123: "H", 5125: "I", 5126: "f"}[accessor["componentType"]]
    size = struct.calcsize("<" + code * components)
    stride = view.get("byteStride", size)
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return [
        struct.unpack_from("<" + code * components, binary, offset + item * stride)
        for item in range(accessor["count"])
    ]


def append_view(document: dict, binary: bytearray, payload: bytes, target: int) -> int:
    align_four(binary)
    offset = len(binary)
    binary.extend(payload)
    view = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload), "target": target}
    document["bufferViews"].append(view)
    return len(document["bufferViews"]) - 1


def largest_lower_body_component(
    positions: list[tuple[float, ...]], indices: list[int]
) -> list[int]:
    # 先以人體座標裁出腰部至腳踝；X 限制排除同高度的手腕與手指。
    triangles: list[tuple[int, int, int]] = []
    for offset in range(0, len(indices), 3):
        triangle = tuple(indices[offset : offset + 3])
        vertices = [positions[index] for index in triangle]
        if all(0.08 <= point[1] <= 1.06 and abs(point[0]) <= 0.42 for point in vertices):
            triangles.append(triangle)

    touching: dict[int, list[int]] = defaultdict(list)
    for triangle_index, triangle in enumerate(triangles):
        for vertex in triangle:
            touching[vertex].append(triangle_index)

    components: list[list[int]] = []
    visited: set[int] = set()
    for first in range(len(triangles)):
        if first in visited:
            continue
        stack = [first]
        visited.add(first)
        component: list[int] = []
        while stack:
            current = stack.pop()
            component.append(current)
            for vertex in triangles[current]:
                for neighbour in touching[vertex]:
                    if neighbour not in visited:
                        visited.add(neighbour)
                        stack.append(neighbour)
        components.append(component)

    if not components:
        raise ValueError("pants_surface_not_found")
    selected = max(components, key=len)
    if len(selected) < 2500:
        raise ValueError("pants_surface_incomplete")
    return [vertex for triangle_index in selected for vertex in triangles[triangle_index]]


def build(input_path: Path, output_path: Path) -> None:
    document, binary = read_glb(input_path)
    if any(node.get("name") == "Pants" for node in document.get("nodes", [])):
        raise ValueError("pants_node_already_exists")

    body_node = next(node for node in document["nodes"] if node.get("name") == "Body")
    body_mesh = document["meshes"][body_node["mesh"]]
    primitive = body_mesh["primitives"][0]
    positions = decode_accessor(document, binary, primitive["attributes"]["POSITION"])
    normals = decode_accessor(document, binary, primitive["attributes"]["NORMAL"])
    source_indices = [value[0] for value in decode_accessor(document, binary, primitive["indices"])]
    pants_indices = largest_lower_body_component(positions, source_indices)

    # 沿既有法線外推 7 mm，避免與裸體基底發生深度閃爍。
    pants_positions = [
        tuple(position[axis] + normal[axis] * 0.007 for axis in range(3))
        for position, normal in zip(positions, normals, strict=True)
    ]
    if not all(math.isfinite(value) for point in pants_positions for value in point):
        raise ValueError("non_finite_pants_position")

    position_bytes = b"".join(struct.pack("<3f", *point) for point in pants_positions)
    position_view = append_view(document, binary, position_bytes, 34962)
    position_accessor = {
        "bufferView": position_view,
        "componentType": 5126,
        "count": len(pants_positions),
        "type": "VEC3",
        "min": [min(point[axis] for point in pants_positions) for axis in range(3)],
        "max": [max(point[axis] for point in pants_positions) for axis in range(3)],
    }
    document["accessors"].append(position_accessor)
    position_index = len(document["accessors"]) - 1

    index_component = document["accessors"][primitive["indices"]]["componentType"]
    index_code = {5123: "H", 5125: "I"}[index_component]
    index_bytes = struct.pack("<" + index_code * len(pants_indices), *pants_indices)
    index_view = append_view(document, binary, index_bytes, 34963)
    document["accessors"].append(
        {
            "bufferView": index_view,
            "componentType": index_component,
            "count": len(pants_indices),
            "type": "SCALAR",
            "min": [min(pants_indices)],
            "max": [max(pants_indices)],
        }
    )
    index_index = len(document["accessors"]) - 1

    document["materials"].append(
        {
            "name": "pants_AevryndBlackCloth",
            "doubleSided": True,
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.012, 0.016, 0.022, 1.0],
                "metallicFactor": 0.04,
                "roughnessFactor": 0.62,
            },
        }
    )
    material_index = len(document["materials"]) - 1
    attributes = dict(primitive["attributes"])
    attributes["POSITION"] = position_index
    document["meshes"].append(
        {
            "name": "Pants",
            "primitives": [
                {
                    "attributes": attributes,
                    "indices": index_index,
                    "material": material_index,
                    "mode": 4,
                }
            ],
        }
    )
    pants_node = {
        "name": "Pants",
        "mesh": len(document["meshes"]) - 1,
        "skin": body_node["skin"],
        "extras": {"component": "Pants", "clothing": True, "fit": "body_surface_offset_7mm"},
    }
    document["nodes"].append(pants_node)
    document["scenes"][document.get("scene", 0)]["nodes"].append(len(document["nodes"]) - 1)
    document["asset"]["generator"] = "Aevrynd exact-third-image export 136 with fitted pants"
    document.setdefault("extras", {})["clothingToggle"] = "Hide Upper and Pants nodes"
    document["extras"]["pantsTriangleCount"] = len(pants_indices) // 3
    document["buffers"][0]["byteLength"] = len(binary)

    json_bytes = json.dumps(document, separators=(",", ":"), allow_nan=False).encode("utf-8")
    json_payload = bytearray(json_bytes)
    align_four(json_payload, 0x20)
    align_four(binary)
    total = 12 + 8 + len(json_payload) + 8 + len(binary)
    output = bytearray(struct.pack("<III", GLB_MAGIC, 2, total))
    output.extend(struct.pack("<II", len(json_payload), JSON_CHUNK))
    output.extend(json_payload)
    output.extend(struct.pack("<II", len(binary), BIN_CHUNK))
    output.extend(binary)
    output_path.write_bytes(output)
    print(
        json.dumps(
            {
                "output": str(output_path),
                "bytes": len(output),
                "pantsTriangles": len(pants_indices) // 3,
                "pantsUniqueVertices": len(set(pants_indices)),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    build(arguments.input, arguments.output)
