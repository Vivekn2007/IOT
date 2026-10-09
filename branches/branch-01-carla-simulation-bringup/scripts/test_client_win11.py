#!/usr/bin/env python3
"""
test_client_win11.py
-------------------------------------------------------------------------------
Simple test client demonstrating how any team member on Windows 11 connects
to Person 1's live sensor stream using ZeroMQ.
-------------------------------------------------------------------------------
"""

import zmq
import json
import time

def main():
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://127.0.0.1:5555")

    # Subscribe to all topics or select specific ones: b'camera', b'radar', b'ultrasonic', b'imu'
    sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
    print(">>> Subscribed to tcp://127.0.0.1:5555. Listening for multi-modal frames...")

    count = 0
    start = time.time()

    try:
        while True:
            parts = sub_socket.recv_multipart()
            topic = parts[0].decode('utf-8')
            count += 1

            if topic == 'camera':
                header = json.loads(parts[1].decode('utf-8'))
                img_bytes = len(parts[2])
                print(f"[RECV: CAMERA] Frame {header['frame']} | Size: {header['width']}x{header['height']} ({img_bytes} bytes)")
            elif topic == 'radar':
                data = json.loads(parts[1].decode('utf-8'))
                print(f"[RECV: RADAR] Frame {data['frame']} | Targets: {data['count']} points detected")
            elif topic == 'ultrasonic':
                data = json.loads(parts[1].decode('utf-8'))
                print(f"[RECV: SONAR] Frame {data['frame']} | Points: {data['points_count']}")
            elif topic == 'imu':
                data = json.loads(parts[1].decode('utf-8'))
                az = data['accel']['z']
                print(f"[RECV: IMU] Frame {data['frame']} | Z-Accel: {az:+.2f} m/s²")

    except KeyboardInterrupt:
        print("\nExiting listener...")
    finally:
        sub_socket.close()
        context.term()

if __name__ == '__main__':
    main()
