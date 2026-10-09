#!/usr/bin/env python3
"""
weather_and_pothole_spawner.py
-------------------------------------------------------------------------------
Part of Person 1's Module: CARLA Digital Twin Weather Controls & Dense Pothole Spawner.
Upgraded version:
  - Spawns 25+ road hazard obstacles across BOTH lanes of the road.
  - Staggered in a grid pattern: varying lane offsets (-1.5m, 0m, +1.5m) at
    multiple forward distances (5m, 10m, 15m, 20m, 30m, 40m, 50m, 65m, 80m).
  - Applies full Indian Monsoon weather (100% rain, 100% puddles, 75% fog).
-------------------------------------------------------------------------------
"""

import sys
import time
import argparse
import random

try:
    import carla
except ImportError:
    print("[ERROR] 'carla' Python package not found.")
    print("Install: pip install D:\\CARLA_0.9.16\\PythonAPI\\carla\\dist\\carla-0.9.16-cp312-cp312-win_amd64.whl")
    sys.exit(1)

def apply_monsoon_weather(world):
    print(">>> Injecting Indian Monsoon Weather...")
    world.set_weather(carla.WeatherParameters(
        cloudiness=95.0,
        precipitation=100.0,
        precipitation_deposits=100.0,
        wind_intensity=65.0,
        sun_azimuth_angle=20.0,
        sun_altitude_angle=15.0,
        fog_density=75.0,
        fog_distance=15.0,
        fog_falloff=0.2,
        wetness=100.0
    ))
    print("    [OK] 100% Precipitation | 100% Puddles | 75% Fog applied.")

def spawn_dense_potholes(world, ego_vehicle):
    """
    Spawns a dense grid of pothole hazards in both lanes ahead of the vehicle.
    Distances: 5m to 80m
    Lane offsets: -2.0m (left lane), -0.5m (left-center), +0.5m (right-center), +2.0m (right lane)
    """
    blueprint_library = world.get_blueprint_library()

    # Use static cone/debris props as pothole markers in CARLA
    prop_candidates = [
        'static.prop.dirtdebris01',
        'static.prop.dirtdebris02',
        'static.prop.garbage01',
        'static.prop.garbage02',
        'static.prop.garbage03',
    ]

    # Try to find a usable static prop
    hazard_bp = None
    for prop_name in prop_candidates:
        bp = blueprint_library.find(prop_name)
        if bp:
            hazard_bp = bp
            break

    if hazard_bp is None:
        # Fallback: use any static prop available
        static_props = blueprint_library.filter('static.prop.*')
        if static_props:
            hazard_bp = static_props[0]
        else:
            print("    [WARN] No static props found. Cannot spawn physical pothole markers.")
            return []

    ego_transform = ego_vehicle.get_transform()
    fwd = ego_transform.get_forward_vector()
    right = ego_transform.get_right_vector()

    # Dense pothole grid configuration:
    # Each row has a forward distance and several lateral lane offsets
    pothole_grid = []

    # Near zone: 5m – 20m ahead (high density - these ARE visible to camera)
    for dist in [4.0, 6.0, 8.5, 11.0, 13.5, 16.0, 18.5, 20.0]:
        for lateral in [-2.0, -0.7, 0.7, 2.0]:
            pothole_grid.append((dist, lateral))

    # Mid zone: 25m – 50m ahead
    for dist in [25.0, 30.0, 35.0, 40.0, 45.0, 50.0]:
        for lateral in [-1.5, 0.0, 1.5]:
            pothole_grid.append((dist, lateral))

    # Far zone: 55m – 80m ahead (detected by 77 GHz radar)
    for dist in [55.0, 65.0, 75.0, 80.0]:
        for lateral in [-1.0, 0.5]:
            pothole_grid.append((dist, lateral))

    print(f">>> Spawning {len(pothole_grid)} road hazard markers in dense pothole grid...")
    spawned = []

    for dist, lateral in pothole_grid:
        loc = carla.Location(
            x = ego_transform.location.x + fwd.x * dist + right.x * lateral,
            y = ego_transform.location.y + fwd.y * dist + right.y * lateral,
            z = ego_transform.location.z - 0.02   # Flush with road surface
        )
        rot = ego_transform.rotation
        actor = world.try_spawn_actor(hazard_bp, carla.Transform(loc, rot))
        if actor:
            spawned.append(actor)

    print(f"    [OK] Successfully spawned {len(spawned)} of {len(pothole_grid)} pothole markers.")
    print(f"    Distributed across 3 zones: Near (4-20m), Mid (25-50m), Far (55-80m)")
    print(f"    Lateral spread: across left lane, centre, and right lane.")
    return spawned

def main():
    parser = argparse.ArgumentParser(description="CARLA Dense Pothole Spawner & Monsoon Injector")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2000)
    parser.add_argument("--respawn-interval", type=int, default=0,
                        help="If >0, re-spawn potholes every N seconds (for looping roads)")
    args = parser.parse_args()

    print(f">>> Connecting to CARLA at {args.host}:{args.port}...")
    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(10.0)
        world = client.get_world()
        print(">>> Connected to CARLA World.")
    except Exception as e:
        print(f"[FATAL] Cannot connect to CARLA: {e}")
        sys.exit(1)

    # 1. Monsoon weather
    apply_monsoon_weather(world)

    # 2. Find ego vehicle
    ego_vehicle = None
    for actor in world.get_actors():
        if actor.attributes.get('role_name') == 'ego_vehicle':
            ego_vehicle = actor
            break

    if not ego_vehicle:
        print("[WARN] No ego_vehicle found yet. Run start_broadcaster.bat first, then rerun this script.")
        sys.exit(1)

    print(f">>> Ego vehicle found (ID: {ego_vehicle.id}).")

    spawned_actors = spawn_dense_potholes(world, ego_vehicle)

    if args.respawn_interval > 0:
        print(f"\n>>> Auto-respawn mode active (every {args.respawn_interval}s). Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(args.respawn_interval)
                print(">>> Refreshing pothole positions...")
                for a in spawned_actors:
                    try:
                        a.destroy()
                    except Exception:
                        pass
                spawned_actors = spawn_dense_potholes(world, ego_vehicle)
        except KeyboardInterrupt:
            print("\n>>> Cleaning up all pothole actors...")
            for a in spawned_actors:
                try:
                    a.destroy()
                except Exception:
                    pass
    else:
        print("\n>>> Dense pothole grid is now active in the simulation!")
        print(">>> Potholes are visible in your CARLA window and detectable by the Vision HUD.")
        print(">>> Close this window when done.")

if __name__ == "__main__":
    main()
