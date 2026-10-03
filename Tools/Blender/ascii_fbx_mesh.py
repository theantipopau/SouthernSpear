# Southern Spear - read the geometry out of an ASCII FBX (Blender's importer refuses ASCII FBX).
# Used for the Fab "Gloves for fps game" hands (Content/Sourced/Gloves/source/Hands.fbx, CC BY 4.0, Bobeer).
# Returns [(name, verts[(x,y,z)], polys[[vi..]], uv_per_loop[(u,v)])]; geometry only, no skinning.
import re


def _array(block, key):
    m = re.search(key + r":\s*\*\d+\s*\{\s*a:\s*([^}]*)\}", block)
    return [float(x) for x in m.group(1).replace("\n", "").replace("\t", "").split(",") if x.strip()] if m else []


def read(path):
    text = open(path, encoding="utf8", errors="ignore").read()
    out = []
    names = dict(re.findall(r'Model: (\d+), "Model::([^"]+)", "Mesh"', text))
    conns = re.findall(r"C: \"OO\",(\d+),(\d+)", text)
    geo_to_model = {int(a): b for a, b in conns}
    for m in re.finditer(r'\tGeometry: (\d+), "Geometry::", "Mesh" \{', text):
        gid = int(m.group(1))
        start = m.end()
        nxt = text.find("\n\tGeometry:", start)
        end = nxt if nxt != -1 else text.find("\n\tMaterial:", start)
        block = text[start:end]
        v = _array(block, "Vertices")
        idx = [int(x) for x in _array(block, "PolygonVertexIndex")]
        uvm = re.search(r"LayerElementUV:.*?UV:\s*\*\d+\s*\{\s*a:\s*([^}]*)\}.*?UVIndex:\s*\*\d+\s*\{\s*a:\s*([^}]*)\}", block, re.S)
        uvs = [float(x) for x in uvm.group(1).replace("\n", "").replace("\t", "").split(",") if x.strip()]
        uvi = [int(x) for x in uvm.group(2).replace("\n", "").replace("\t", "").split(",") if x.strip()]
        verts = [(v[i], v[i + 1], v[i + 2]) for i in range(0, len(v), 3)]
        polys, cur = [], []
        for i in idx:
            if i < 0:
                cur.append(~i)
                polys.append(cur)
                cur = []
            else:
                cur.append(i)
        loopuv = [(uvs[2 * i], uvs[2 * i + 1]) for i in uvi]
        out.append((names.get(str(geo_to_model.get(gid)), "geo%d" % gid), verts, polys, loopuv))
    return out
