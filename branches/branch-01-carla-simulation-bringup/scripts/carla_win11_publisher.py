#!/usr/bin/env python3
"""
carla_win11_publisher.py
-------------------------------------------------------------------------------
100% PURE WINDOWS 11 SENSOR BROADCASTER (ZeroMQ Publisher)
  - Moves CARLA spectator camera behind ego vehicle (Third-person chase cam).
  - High-performance JPEG compressed camera streaming to avoid ZMQ queue saturation.
  - Thread-safe pub_socket transmission using threading.Lock.
  - Broadcasts to: tcp://127.0.0.1:5555
-------------------------------------------------------------------------------
"""

import sys
import time
import json
import threading
import numpy as np

try:
    import carla
except ImportError:
    print("[ERROR] carla package missing.")
    sys.exit(1)

try:
    import zmq
except ImportError:
    print("[ERROR] pyzmq missing.")
    sys.exit(1)

try:
    import cv2
except ImportError:
    cv2 = None

def main():
    print("==========================================================================")
    print("  CARLA 0.9.16 WINDOWS 11 BROADCASTER WITH SPECTATOR CHASE CAM            ")
    print("  Broadcasting to: tcp://127.0.0.1:5555                                  ")
    print("==========================================================================")

    # Thread-safe ZeroMQ publisher
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.SNDHWM, 50)  # High watermark to avoid queue backup
    pub_socket.bind("tcp://127.0.0.1:5555")
    send_lock = threading.Lock()
    print(">>> ZeroMQ Publisher bound to port 5555.")

    actor_list = []
    
    try:
        # 1. Connect to CARLA
        print(">>> Connecting to CARLA on 127.0.0.1:2000 (timeout: 30s)...")
        client = carla.Client("127.0.0.1", 2000)
        client.set_timeout(30.0)
        try:
            world = client.get_world()
        except RuntimeError as e:
            print("\n[ERROR] Could not connect to CARLA at 127.0.0.1:2000.")
            print(">>> Please make sure CARLA is running first by double-clicking 'start_carla.bat'!")
            print(">>> Wait 5-10 seconds until the Unreal Engine window opens, then run this script again.\n")
            return
        bp_library = world.get_blueprint_library()
        spectator = world.get_spectator()

        # 2. Apply Monsoon Weather Preset
        print(">>> Injecting Monsoon Weather (100% Rain, 100% Puddles, 75% Fog)...")
        world.set_weather(carla.WeatherParameters(
            cloudiness=95.0,
            precipitation=100.0,
            precipitation_deposits=100.0,
            wind_intensity=60.0,
            fog_density=75.0,
            fog_distance=15.0,
            wetness=100.0,
            sun_azimuth_angle=20.0,
            sun_altitude_angle=15.0
        ))

        # 3. Spawn Ego-Vehicle
        spawn_points = world.get_map().get_spawn_points()
        spawn_point = spawn_points[0] if spawn_points else carla.Transform()
        vehicle_bp = bp_library.filter('vehicle.lincoln.mkz_2020')[0]
        vehicle_bp.set_attribute('role_name', 'ego_vehicle')
        ego_vehicle = world.spawn_actor(vehicle_bp, spawn_point)
        actor_list.append(ego_vehicle)
        ego_vehicle.set_autopilot(True)
        print(f">>> Ego-Vehicle spawned (ID: {ego_vehicle.id}). Autopilot engaged.")

        # 4. Sensor 1: Front Optical RGB Camera
        cam_bp = bp_library.find('sensor.camera.rgb')
        cam_bp.set_attribute('image_size_x', '1280')
        cam_bp.set_attribute('image_size_y', '720')
        cam_bp.set_attribute('fov', '70.0')
        cam_bp.set_attribute('sensor_tick', '0.033') # ~30 FPS
        cam_transform = carla.Transform(carla.Location(x=1.2, y=0.0, z=1.3), carla.Rotation(pitch=-2.0))
        camera = world.spawn_actor(cam_bp, cam_transform, attach_to=ego_vehicle)
        actor_list.append(camera)

        def on_cam(img):
            header = json.dumps({'width': img.width, 'height': img.height, 'frame': img.frame, 'timestamp': img.timestamp}).encode('utf-8')
            # Fast JPEG compression
            if cv2 is not None:
                bgra = np.frombuffer(img.raw_data, dtype=np.uint8).reshape((img.height, img.width, 4))
                bgr = cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)
                _, jpeg_bytes = cv2.imencode('.jpg', bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                payload_bytes = jpeg_bytes.tobytes()
            else:
                payload_bytes = bytes(img.raw_data)

            with send_lock:
                pub_socket.send_multipart([b'camera', header, payload_bytes])

        camera.listen(on_cam)
        print("    [ONLINE] Front Camera: 720p @ 30 FPS -> topic 'camera'")

        # 5. Sensor 2: 77 GHz mmWave Radar
        radar_bp = bp_library.find('sensor.other.radar')
        radar_bp.set_attribute('horizontal_fov', '60.0')
        radar_bp.set_attribute('vertical_fov', '20.0')
        radar_bp.set_attribute('range', '150.0')
        radar_bp.set_attribute('points_per_second', '25000')
        radar_bp.set_attribute('sensor_tick', '0.05') # ~20 Hz
        radar_transform = carla.Transform(carla.Location(x=2.3, y=0.0, z=0.5), carla.Rotation(pitch=-1.5))
        radar = world.spawn_actor(radar_bp, radar_transform, attach_to=ego_vehicle)
        actor_list.append(radar)

        def on_radar(data):
            points = []
            for detect in data:
                points.append({
                    'depth': detect.depth,
                    'azimuth': detect.azimuth,
                    'altitude': detect.altitude,
                    'velocity': detect.velocity
                })
            payload = json.dumps({'frame': data.frame, 'count': len(points), 'points': points}).encode('utf-8')
            with send_lock:
                pub_socket.send_multipart([b'radar', payload])

        radar.listen(on_radar)
        print("    [ONLINE] 77 GHz Radar: 150m Range @ 20 Hz -> topic 'radar'")

        # 6. Sensor 3: Downward Ultrasonic Array (Ray-cast pointing -90 deg down)
        sonar_bp = bp_library.find('sensor.lidar.ray_cast')
        sonar_bp.set_attribute('range', '3.0')
        sonar_bp.set_attribute('channels', '4')
        sonar_bp.set_attribute('points_per_second', '4000')
        sonar_bp.set_attribute('rotation_frequency', '50')
        sonar_bp.set_attribute('sensor_tick', '0.02')
        sonar_transform = carla.Transform(carla.Location(x=1.0, y=0.0, z=0.35), carla.Rotation(pitch=-90.0))
        sonar = world.spawn_actor(sonar_bp, sonar_transform, attach_to=ego_vehicle)
        actor_list.append(sonar)

        under_chassis_state = {'active': False, 'depth_cm': 0.0}

        def on_sonar(data):
            depth_m = 0.35 + (under_chassis_state['depth_cm'] / 100.0 if under_chassis_state['active'] else 0.0)
            payload = json.dumps({
                'frame': data.frame,
                'points_count': len(data),
                'measured_distance_m': round(depth_m, 4),
                'is_pothole_active': under_chassis_state['active'],
                'depth_cm': round(under_chassis_state['depth_cm'], 1)
            }).encode('utf-8')
            with send_lock:
                pub_socket.send_multipart([b'ultrasonic', payload])

        sonar.listen(on_sonar)
        print("    [ONLINE] Downward Sonar: 50 Hz Under-Chassis -> topic 'ultrasonic'")

        # 7. Sensor 4: 6-Axis IMU
        imu_bp = bp_library.find('sensor.other.imu')
        imu_bp.set_attribute('sensor_tick', '0.01')
        imu_transform = carla.Transform(carla.Location(x=0.0, y=0.0, z=0.2))
        imu = world.spawn_actor(imu_bp, imu_transform, attach_to=ego_vehicle)
        actor_list.append(imu)

        def on_imu(data):
            shock_z = 0.0
            if under_chassis_state['active']:
                shock_z = np.random.uniform(12.0, 22.0) # Upward suspension compression kick
            payload = json.dumps({
                'frame': data.frame,
                'accel': {'x': data.accelerometer.x, 'y': data.accelerometer.y, 'z': data.accelerometer.z + shock_z},
                'gyro': {'x': data.gyroscope.x, 'y': data.gyroscope.y, 'z': data.gyroscope.z}
            }).encode('utf-8')
            with send_lock:
                pub_socket.send_multipart([b'imu', payload])

        imu.listen(on_imu)
        print("    [ONLINE] 6-Axis IMU: 100 Hz Center of Mass -> topic 'imu'")

        print("\n>>> Broadcasting active on tcp://127.0.0.1:5555.")
        print(">>> Spectator camera locked in chase mode. Watch your CARLA window!")
        print(">>> Press Ctrl+C in this terminal to stop.\n")

        # 8. Main Loop with Spectator Chase Camera
        last_log = time.time()
        while True:
            # Update spectator camera to smoothly follow the vehicle
            v_transform = ego_vehicle.get_transform()
            fwd = v_transform.get_forward_vector()
            right = v_transform.get_right_vector()
            # 6.5m behind, 2.8m above
            cam_loc = v_transform.location - fwd * 6.5 + carla.Location(z=2.8)
            cam_rot = carla.Rotation(pitch=-15.0, yaw=v_transform.rotation.yaw, roll=0.0)
            spectator.set_transform(carla.Transform(cam_loc, cam_rot))

            # Query ground-truth pothole props in the world
            now = time.time()
            all_actors = world.get_actors()
            gt_potholes = []
            under_chassis_pothole = None

            for a in all_actors:
                if 'static.prop' in a.type_id:
                    a_loc = a.get_location()
                    dx = a_loc.x - v_transform.location.x
                    dy = a_loc.y - v_transform.location.y
                    # Project to vehicle local coordinates
                    fwd_dist = dx * fwd.x + dy * fwd.y
                    lat_dist = dx * right.x + dy * right.y
                    
                    if 0.0 < fwd_dist < 85.0 and abs(lat_dist) < 5.0:
                        true_d_cm = round(7.5 + (hash(a.id) % 60) / 10.0, 1) # 7.5 - 13.5 cm
                        gt_potholes.append({
                            'id': a.id,
                            'true_distance_m': round(fwd_dist, 2),
                            'true_lateral_m': round(lat_dist, 2),
                            'true_depth_cm': true_d_cm,
                            'is_waterlogged': True
                        })
                    if 0.0 < fwd_dist < 2.0 and abs(lat_dist) < 1.2:
                        under_chassis_pothole = a
                        under_chassis_state['active'] = True
                        under_chassis_state['depth_cm'] = true_d_cm

            if under_chassis_pothole is None:
                under_chassis_state['active'] = False
                under_chassis_state['depth_cm'] = 0.0

            # Publish Ground Truth topic every tick
            gt_payload = json.dumps({'time': now, 'potholes': sorted(gt_potholes, key=lambda p: p['true_distance_m'])}).encode('utf-8')
            with send_lock:
                pub_socket.send_multipart([b'ground_truth', gt_payload])

            # Periodic status print
            if now - last_log >= 1.0:
                vel = ego_vehicle.get_velocity()
                speed = 3.6 * ((vel.x**2 + vel.y**2 + vel.z**2)**0.5)
                print(f"[STATUS] Speed: {speed:>4.1f} km/h | Potholes Ahead: {len(gt_potholes)} | Streaming Active")
                last_log = now

            time.sleep(0.04) # ~25 Hz smooth chase camera update

    except KeyboardInterrupt:
        print("\n>>> User stopped simulation (Ctrl+C)...")
    finally:
        print(">>> Destroying vehicle and sensor actors...")
        for a in reversed(actor_list):
            if a and a.is_alive:
                a.destroy()
        pub_socket.close()
        context.term()
        print(">>> Cleaned up successfully.")

if __name__ == '__main__':
    main()
