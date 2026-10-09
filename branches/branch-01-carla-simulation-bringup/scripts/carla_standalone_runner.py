#!/usr/bin/env python3
"""
carla_standalone_runner.py
-------------------------------------------------------------------------------
Native Windows 10/11 runner for CARLA 0.9.16.
Location of CARLA: D:\CARLA_0.9.16\CarlaUE4.exe

This script runs directly on Windows using Python 3.12 without requiring Linux/WSL2.
It:
  1. Connects to CARLA 0.9.16 server (port 2000).
  2. Sets severe Indian monsoon weather (100% rain, 100% puddles, 75% fog).
  3. Spawns an ego-vehicle and enables autopilot.
  4. Mounts all 4 perception sensors (RGB Camera, 77GHz Radar, Downward Ultrasonic, IMU).
  5. Listens to all 4 streams, calculating live FPS and displaying a telemetry HUD.
  6. Automatically cleans up all actors on exit (Ctrl+C).
-------------------------------------------------------------------------------
"""

import sys
import time
import os

try:
    import carla
except ImportError:
    print("[ERROR] CARLA Python package not found. Run: pip install D:\\CARLA_0.9.16\\PythonAPI\\carla\\dist\\carla-0.9.16-cp312-cp312-win_amd64.whl")
    sys.exit(1)

def main():
    print("==========================================================================")
    print("  CARLA 0.9.16 MULTI-MODAL PERCEPTION RIG (WINDOWS NATIVE RUNNER)         ")
    print("  CARLA Path: D:\\CARLA_0.9.16\\CarlaUE4.exe                                ")
    print("==========================================================================")

    actor_list = []
    stats = {
        'camera': {'count': 0, 'last': time.time(), 'fps': 0.0},
        'radar': {'count': 0, 'last': time.time(), 'fps': 0.0, 'points': 0},
        'ultrasonic': {'count': 0, 'last': time.time(), 'fps': 0.0, 'range': 0.0},
        'imu': {'count': 0, 'last': time.time(), 'fps': 0.0, 'az': 0.0}
    }

    try:
        # 1. Connect to CARLA
        print(">>> Connecting to CARLA server on 127.0.0.1:2000...")
        client = carla.Client("127.0.0.1", 2000)
        client.set_timeout(10.0)
        world = client.get_world()
        bp_library = world.get_blueprint_library()
        print(f">>> Connected to map: '{world.get_map().name}'")

        # 2. Inject Monsoon Weather
        print(">>> Applying Indian Monsoon Weather preset...")
        monsoon = carla.WeatherParameters(
            cloudiness=95.0,
            precipitation=100.0,          # Torrential rain
            precipitation_deposits=100.0, # Saturated water puddles on road
            wind_intensity=60.0,
            fog_density=75.0,             # Optical occlusion
            fog_distance=15.0,
            wetness=100.0,
            sun_azimuth_angle=20.0,
            sun_altitude_angle=15.0
        )
        world.set_weather(monsoon)
        print("    [OK] Weather: 100% Rain, 100% Puddles, 75% Fog applied.")

        # 3. Spawn Ego-Vehicle
        spawn_points = world.get_map().get_spawn_points()
        if not spawn_points:
            print("[FATAL] No spawn points found in current map.")
            return

        vehicle_bp = bp_library.filter('vehicle.lincoln.mkz_2020')[0] or bp_library.filter('vehicle.*')[0]
        vehicle_bp.set_attribute('role_name', 'ego_vehicle')
        spawn_point = spawn_points[0]
        ego_vehicle = world.spawn_actor(vehicle_bp, spawn_point)
        actor_list.append(ego_vehicle)
        print(f">>> Ego-Vehicle spawned (ID: {ego_vehicle.id}) at ({spawn_point.location.x:.1f}, {spawn_point.location.y:.1f})")

        # Enable vehicle autopilot
        ego_vehicle.set_autopilot(True)

        # 4. Mount Sensor 1: Front Optical RGB Camera
        cam_bp = bp_library.find('sensor.camera.rgb')
        cam_bp.set_attribute('image_size_x', '1280')
        cam_bp.set_attribute('image_size_y', '720')
        cam_bp.set_attribute('fov', '70.0')
        cam_bp.set_attribute('sensor_tick', '0.033') # ~30 FPS
        cam_transform = carla.Transform(carla.Location(x=1.2, y=0.0, z=1.3), carla.Rotation(pitch=-2.0))
        camera = world.spawn_actor(cam_bp, cam_transform, attach_to=ego_vehicle)
        actor_list.append(camera)

        def on_camera_frame(image):
            now = time.time()
            dt = now - stats['camera']['last']
            if dt > 0:
                stats['camera']['fps'] = 0.8 * stats['camera']['fps'] + 0.2 * (1.0 / dt)
            stats['camera']['last'] = now
            stats['camera']['count'] += 1

        camera.listen(on_camera_frame)
        print("    [MOUNTED] Front RGB Camera: (1.2m, 0.0m, 1.3m) -> 720p @ 30 FPS")

        # 5. Mount Sensor 2: 77 GHz mmWave FMCW Radar
        radar_bp = bp_library.find('sensor.other.radar')
        radar_bp.set_attribute('horizontal_fov', '60.0')
        radar_bp.set_attribute('vertical_fov', '20.0')
        radar_bp.set_attribute('range', '150.0')
        radar_bp.set_attribute('points_per_second', '25000')
        radar_bp.set_attribute('sensor_tick', '0.05') # ~20 Hz
        radar_transform = carla.Transform(carla.Location(x=2.3, y=0.0, z=0.5), carla.Rotation(pitch=-1.5))
        radar = world.spawn_actor(radar_bp, radar_transform, attach_to=ego_vehicle)
        actor_list.append(radar)

        def on_radar_data(radar_data):
            now = time.time()
            dt = now - stats['radar']['last']
            if dt > 0:
                stats['radar']['fps'] = 0.8 * stats['radar']['fps'] + 0.2 * (1.0 / dt)
            stats['radar']['last'] = now
            stats['radar']['count'] += 1
            stats['radar']['points'] = len(radar_data)

        radar.listen(on_radar_data)
        print("    [MOUNTED] 77 GHz mmWave Radar: (2.3m, 0.0m, 0.5m) -> 150m Range @ 20 Hz")

        # 6. Mount Sensor 3: Downward Ultrasonic Acoustic Ray-Cast
        # Pitch = -90 degrees (pointing straight down through undercarriage to road)
        sonar_bp = bp_library.find('sensor.lidar.ray_cast')
        sonar_bp.set_attribute('range', '3.0')
        sonar_bp.set_attribute('channels', '4')
        sonar_bp.set_attribute('points_per_second', '4000')
        sonar_bp.set_attribute('rotation_frequency', '50') # 50 Hz
        sonar_bp.set_attribute('sensor_tick', '0.02')
        sonar_transform = carla.Transform(carla.Location(x=1.0, y=0.0, z=0.35), carla.Rotation(pitch=-90.0))
        sonar = world.spawn_actor(sonar_bp, sonar_transform, attach_to=ego_vehicle)
        actor_list.append(sonar)

        def on_sonar_data(point_cloud):
            now = time.time()
            dt = now - stats['ultrasonic']['last']
            if dt > 0:
                stats['ultrasonic']['fps'] = 0.8 * stats['ultrasonic']['fps'] + 0.2 * (1.0 / dt)
            stats['ultrasonic']['last'] = now
            stats['ultrasonic']['count'] += 1

        sonar.listen(on_sonar_data)
        print("    [MOUNTED] Downward Ultrasonic Array: (1.0m, 0.0m, 0.35m) -> Under-chassis @ 50 Hz")

        # 7. Mount Sensor 4: 6-Axis IMU (MPU6050 emulation)
        imu_bp = bp_library.find('sensor.other.imu')
        imu_bp.set_attribute('sensor_tick', '0.01') # 100 Hz
        imu_transform = carla.Transform(carla.Location(x=0.0, y=0.0, z=0.2))
        imu = world.spawn_actor(imu_bp, imu_transform, attach_to=ego_vehicle)
        actor_list.append(imu)

        def on_imu_data(imu_data):
            now = time.time()
            dt = now - stats['imu']['last']
            if dt > 0:
                stats['imu']['fps'] = 0.8 * stats['imu']['fps'] + 0.2 * (1.0 / dt)
            stats['imu']['last'] = now
            stats['imu']['count'] += 1
            stats['imu']['az'] = imu_data.accelerometer.z

        imu.listen(on_imu_data)
        print("    [MOUNTED] 6-Axis IMU: (0.0m, 0.0m, 0.2m) -> Center of Mass @ 100 Hz")

        print("\n>>> All 4 Perception Modalities Active! Autopilot navigating road...")
        print(">>> Press Ctrl+C in this terminal to safely stop and clean up.\n")

        # 8. Live Dashboard Loop
        while True:
            time.sleep(1.0)
            v_loc = ego_vehicle.get_location()
            v_vel = ego_vehicle.get_velocity()
            speed_kmh = 3.6 * ((v_vel.x**2 + v_vel.y**2 + v_vel.z**2)**0.5)

            print(f"[STATUS] Speed: {speed_kmh:>4.1f} km/h | Pos: ({v_loc.x:>6.1f}, {v_loc.y:>6.1f}) | "
                  f"CAM: {stats['camera']['fps']:>4.1f} FPS | "
                  f"RADAR: {stats['radar']['fps']:>4.1f} Hz ({stats['radar']['points']} pts) | "
                  f"SONAR: {stats['ultrasonic']['fps']:>4.1f} Hz | "
                  f"IMU: {stats['imu']['fps']:>4.1f} Hz (az: {stats['imu']['az']:>+5.2f} m/s²)")

    except KeyboardInterrupt:
        print("\n>>> User requested stop (Ctrl+C). Initiating cleanup...")
    except Exception as e:
        print(f"\n[ERROR] An exception occurred: {e}")
    finally:
        print(">>> Destroying spawned vehicle and virtual sensors...")
        for actor in reversed(actor_list):
            if actor is not None and actor.is_alive:
                actor.destroy()
        print(">>> Cleanup complete. Simulation terminated cleanly.")

if __name__ == '__main__':
    main()
