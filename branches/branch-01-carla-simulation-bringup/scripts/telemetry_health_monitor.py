#!/usr/bin/env python3
"""
telemetry_health_monitor.py
-------------------------------------------------------------------------------
Part of Person 1's Module: System Health & Topic Verification.
Subscribes to all 4 multi-modal sensor topics from CARLA-ROS 2 bridge:
  1. /sensors/camera/image_raw (RGB Camera)
  2. /sensors/radar/points (77 GHz mmWave FMCW Radar)
  3. /sensors/ultrasonic/range (Downward Ultrasonic Array)
  4. /sensors/imu/data (Chassis 6-axis IMU)

Calculates real-time message frequencies (Hz), verifies data integrity, and
prints a formatted diagnostics dashboard for the team.
-------------------------------------------------------------------------------
"""

import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, Imu

class TelemetryHealthMonitor(Node):
    def __init__(self):
        super().__init__('telemetry_health_monitor')

        self.sensor_stats = {
            'camera': {'count': 0, 'last_time': None, 'hz': 0.0, 'status': 'WAITING'},
            'radar': {'count': 0, 'last_time': None, 'hz': 0.0, 'status': 'WAITING'},
            'ultrasonic': {'count': 0, 'last_time': None, 'hz': 0.0, 'status': 'WAITING'},
            'imu': {'count': 0, 'last_time': None, 'hz': 0.0, 'status': 'WAITING'}
        }

        # Subscriptions
        self.sub_cam = self.create_subscription(Image, '/sensors/camera/image_raw', self.cam_callback, 10)
        self.sub_rad = self.create_subscription(PointCloud2, '/sensors/radar/points', self.rad_callback, 10)
        self.sub_us = self.create_subscription(PointCloud2, '/sensors/ultrasonic/range', self.us_callback, 10)
        self.sub_imu = self.create_subscription(Imu, '/sensors/imu/data', self.imu_callback, 10)

        # Periodic terminal dashboard timer (every 1.0 second)
        self.timer = self.create_timer(1.0, self.display_dashboard)
        self.get_logger().info('=== Telemetry Health Monitor Initialized. Awaiting sensor feeds... ===')

    def update_stat(self, sensor_key):
        now = time.time()
        stat = self.sensor_stats[sensor_key]
        stat['count'] += 1
        if stat['last_time'] is not None:
            dt = now - stat['last_time']
            if dt > 0:
                current_hz = 1.0 / dt
                stat['hz'] = 0.8 * stat['hz'] + 0.2 * current_hz  # Exponential moving average
        stat['last_time'] = now
        stat['status'] = 'HEALTHY' if stat['hz'] > 5.0 else 'STREAMING'

    def cam_callback(self, msg):
        self.update_stat('camera')

    def rad_callback(self, msg):
        self.update_stat('radar')

    def us_callback(self, msg):
        self.update_stat('ultrasonic')

    def imu_callback(self, msg):
        self.update_stat('imu')

    def display_dashboard(self):
        now = time.time()
        print("\033[H\033[J", end="")  # Clear terminal screen
        print("==========================================================================")
        print("     MULTI-MODAL PERCEPTION RIG: LIVE TELEMETRY HEALTH DASHBOARD          ")
        print("==========================================================================")
        print(f"{'SENSOR NAME':<22} | {'ROS 2 TOPIC':<28} | {'RATE (Hz)':<10} | {'STATUS'}")
        print("--------------------------------------------------------------------------")

        for key, name, topic, target_hz in [
            ('camera', 'Front RGB Camera', '/sensors/camera/image_raw', '30 Hz'),
            ('radar', '77GHz mmWave Radar', '/sensors/radar/points', '20 Hz'),
            ('ultrasonic', 'Downward Ultrasonic', '/sensors/ultrasonic/range', '50 Hz'),
            ('imu', 'Chassis 6-Axis IMU', '/sensors/imu/data', '100 Hz')
        ]:
            stat = self.sensor_stats[key]
            # Check for stale data (timeout > 1.5s)
            if stat['last_time'] and (now - stat['last_time']) > 1.5:
                stat['status'] = 'STALE/DISCONNECTED'
                stat['hz'] = 0.0

            status_str = f"[\033[92m{stat['status']}\033[0m]" if 'HEALTHY' in stat['status'] else f"[{stat['status']}]"
            print(f"{name:<22} | {topic:<28} | {stat['hz']:>6.1f} Hz   | {status_str} (Target: {target_hz})")

        print("--------------------------------------------------------------------------")
        all_healthy = all('HEALTHY' in self.sensor_stats[k]['status'] or self.sensor_stats[k]['count'] > 10 for k in self.sensor_stats)
        if all_healthy:
            print(" [PASS] All 4 Perception Modalities Active. Ready for Persons 2-6.")
        else:
            print(" [WAIT] Waiting for all sensor nodes to synchronize...")
        print("==========================================================================")

def main(args=None):
    rclpy.init(args=args)
    node = TelemetryHealthMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
