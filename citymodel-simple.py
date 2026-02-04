import osmnx as ox
import numpy as np 
import pyvista as pv 
from shapely.geometry import Polygon, MultiPolygon
from pathlib import Path 
import random 
#exctracting data from osm open source 
# Modify extract_osm_data function to accept coordinates:
def extract_osm_data_coords(lat, lon, radius=200):
    print(f"Downloading OSM data for ({lat}, {lon})...")
    center_point = (lat, lon)
    buildings = ox.features_from_point(
        center_point,
        tags={'building': True},
        dist=radius
    )
    streets = ox.graph_from_point(center_point, dist=radius,
                                   network_type='drive', simplify=False)
    
    buildings = buildings.to_crs(epsg=2154)
    streets = ox.project_graph(streets, to_crs='epsg:2154')
    print(f"Downloaded {len(buildings)} buildings")
    print(f"Downloaded {len(streets.edges)} street segments")
    return buildings, streets

# Usage:
#building footprints
def generate_footprints(buildings):
    footprints = []
    for geom in buildings.geometry:
        if isinstance(geom,MultiPolygon):
            footprints.extend(list(geom.geoms))
        elif isinstance(geom,Polygon):
            footprints.append(geom)
    return footprints


#3d buildings generation
def create_watertight_buildings(coords, height):
  
    # Remove duplicate last coordinate if it matches the first
    if np.allclose(coords[0], coords[-1]):
        coords = coords[:-1]
    
    n_points = len(coords)
    
    # Create 3D points: bottom vertices (z=0) and top vertices (z=height)
    points = []
    
    # Bottom vertices
    for x, y in coords:
        points.append([x, y, 0])
    
    # Top vertices
    for x, y in coords:
        points.append([x, y, height])
    
    points = np.array(points)
    
    # Create faces array in PyVista format: [n_verts, v1, v2, ..., vn, n_verts, ...]
    faces = []
    
    # Bottom face (reversed for correct normal direction)
    faces.append(n_points)  # Number of vertices in this face
    for i in range(n_points - 1, -1, -1):
        faces.append(i)
    
    # Top face
    faces.append(n_points)  # Number of vertices in this face
    for i in range(n_points):
        faces.append(i + n_points)
    
    # Side faces (quads connecting bottom and top)
    for i in range(n_points):
        next_i = (i + 1) % n_points
        
        # Each side face is a quad with 4 vertices
        faces.append(4)  # Number of vertices in this face
        faces.append(i)              # Bottom current
        faces.append(next_i)         # Bottom next
        faces.append(next_i + n_points)  # Top next
        faces.append(i + n_points)   # Top current
    
    return points, faces


def generate_random_color():
    return [random.random() for _ in range(3)]

def extrude_buildings(footprints):
    print("Extruding buildings...")

    # Create empty PyVista mesh for the final city
    city_mesh = pv.PolyData()
    instances_building = []
    for footprint in footprints:
        # Get coordinates from footprint
        coords = np.array(footprint.exterior.coords)

        # Generate random building height (between 10 and 50 meters)
        height = random.uniform(10, 50)

        # Create watertight building geometry
        points, faces = create_watertight_buildings(coords, height)

        # Create building mesh
        building = pv.PolyData(points, np.array(faces))

        # Generate and apply random color
        color = generate_random_color()
        building['color'] = np.tile(color, (building.n_points, 1))
        instances_building.append(building)
        # Add to city mesh
        if city_mesh.n_points == 0:
            city_mesh = building
        else:
            city_mesh = city_mesh.merge(building, merge_points=False)

    print("Building extrusion complete")
    return city_mesh, instances_building

'''#test for visualisation
location = "Toulouse, France"
radius = 200
buildings, streets = extract_osm_data(location, radius)
footprints = generate_footprints(buildings)
mesh, bd_instances = extrude_buildings(footprints)

pl = pv.Plotter(border=False)
pl.add_mesh(mesh, scalars=mesh['color'], cmap="tab20", show_edges=False)
pl.remove_scalar_bar()
pl.show(title='(C) Florent Poux - 3D Tech')'''

#export building function
def save_to_obj(mesh, output_path):
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"saving model to {output_path}")
    mesh.save(output_path)
    print("export completed")

def streetGraph_to_pyvista(st_graph):
    # Convert the graph to a dataframe
    nodes, edges = ox.graph_to_gdfs(st_graph)
    
    # Convert the edges to a pyvista PolyData object with lines
    pts_list = edges['geometry'].apply(lambda g: np.column_stack(
        (g.xy[0], g.xy[1], np.zeros(len(g.xy[0]))))).tolist()
    vertices = np.concatenate(pts_list)
    
    lines = []  # Create an empty array with 3 columns
    
    j = 0
    
    for i in range(len(pts_list)):
        pts = pts_list[i]
        vertex_length = len(pts)
        vertex_start = j
        vertex_end = j + vertex_length - 1
        vertex_arr = [vertex_length] + \
                     list(range(vertex_start, vertex_end + 1))
        lines.append(vertex_arr)
        j += vertex_length
    
    return pv.PolyData(vertices, lines=np.hstack(lines))

def cloudgify(location, mesh, street_mesh, file_path):
    pl = pv.Plotter(off_screen=True, image_scale=1)
    pl.background_color = 'k'
    
    # Ajouter le texte avec la bonne syntaxe
    actor = pl.add_text(
        location,
        position='upper_left',  # ← underscore
        color='lightgrey',
        font_size=26,
    )
    
    pl.add_mesh(mesh, scalars=mesh['color'], cmap="tab20", show_edges=False)
    pl.add_mesh(street_mesh)
    pl.remove_scalar_bar()
    pl.show(auto_close=False)
    
    viewup = [0, 0, 1]
    
    # Create output directory if it doesn't exist
    output_dir = Path(file_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    path = pl.generate_orbital_path(n_points=40, shift=mesh.length,
                                     viewup=viewup, factor=3.0)
    
    # Convertir Path en string pour open_gif
    pl.open_gif(str(output_dir / "model.gif"))
    pl.orbit_on_path(path, write_frames=True, viewup=viewup)
    pl.close()
    
    print("Export of GIF successful")
    return

lat = 48.8584
lon = 2.2945
location_name = "Paris, France"
radius = 1000

buildings, streets = extract_osm_data_coords(lat, lon, radius)
footprints = generate_footprints(buildings)
mesh, bd_instances = extrude_buildings(footprints)
street_mesh = streetGraph_to_pyvista(streets)
pl = pv.Plotter(border=False)
pl.add_mesh(mesh, scalars=mesh['color'], cmap="tab20", show_edges=False)
pl.remove_scalar_bar()
pl.show(title='(C)  3D Tech')
'''output_dir = "output/" + location_name.split(",")[0]
cloudgify(location_name, mesh, street_mesh, output_dir)

output_file = output_dir + "/buildings.obj"
output_streets = output_dir + "/streets.obj"
save_to_obj(mesh, output_file)
save_to_obj(street_mesh, output_streets)'''
