#!/usr/bin/env python3
"""
rl_evasion_policy.py
-------------------------------------------------------------------------------
Reinforcement Learning (RL) Policy for Autonomous Pothole Evasion & Suspension Control.

Replaces hardcoded if-else vehicle guidance with a Learned RL Policy (Pure NumPy):
  - Agent observes continuous multi-modal fused state:
      [distance, lateral_offset, depth, speed, waterlogged, lane_margin_left, lane_margin_right]
  - Chooses optimal action from 6 discrete actions:
      Action 0: CRUISE_MAINTAIN_SPEED
      Action 1: REGEN_BRAKE_DECELERATE
      Action 2: EMERGENCY_BRAKE
      Action 3: EVASIVE_STEER_LEFT
      Action 4: EVASIVE_STEER_RIGHT
      Action 5: ACTIVE_DAMPER_STIFFEN (Pre-impact suspension prep)
  - Trained via Temporal Difference Q-Learning with Linear Function Approximation.
-------------------------------------------------------------------------------
"""

import os
import json
import time
import numpy as np

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)
RL_WEIGHTS_PATH = os.path.join(MODEL_DIR, "pothole_rl_q_weights.json")

ACTION_NAMES = [
    "CRUISE_MAINTAIN_SPEED",
    "REGEN_BRAKE_DECELERATE",
    "EMERGENCY_BRAKE",
    "EVASIVE_STEER_LEFT",
    "EVASIVE_STEER_RIGHT",
    "ACTIVE_DAMPER_STIFFEN"
]

ACTION_GUIDANCE = {
    0: ("Maintain cruising speed", "ok"),
    1: ("Ease off throttle, slow down smoothly", "warn"),
    2: ("Emergency brake! Severe depression ahead", "bad"),
    3: ("Nudge steer left, evade pothole", "warn"),
    4: ("Nudge steer right, evade pothole", "warn"),
    5: ("Stiffen suspension dampers for impact", "bad")
}

class PotholeEvasionEnv:
    """
    Automotive Vehicle Dynamics Simulation Environment for Pothole Avoidance.
    """
    def __init__(self):
        self.lane_width = 3.6 # meters
        self.max_speed = 60.0  # km/h
        self.reset()

    def reset(self):
        self.veh_lat = 0.0 # Vehicle starts in lane center (0m)
        self.veh_speed = float(np.random.uniform(30.0, 55.0)) # km/h
        
        self.pot_dist = float(np.random.uniform(35.0, 70.0)) # m ahead
        self.pot_lat = float(np.random.choice([-1.1, 0.9, -0.2])) # Left wheel, right wheel, center
        self.pot_depth = float(np.random.uniform(6.0, 16.0)) # cm
        self.pot_water = 1.0 if np.random.rand() > 0.4 else 0.0
        self.damper_stiff = False
        
        self.step_count = 0
        return self._get_features()

    def _get_features(self):
        """Extracts 12 basis features for linear Q-value function approximation."""
        left_dist = (self.lane_width / 2.0) + self.veh_lat
        right_dist = (self.lane_width / 2.0) - self.veh_lat
        hit_risk = max(0.0, 1.0 - abs(self.pot_lat - self.veh_lat) / 0.8)
        is_near = 1.0 if self.pot_dist < 20.0 else (0.5 if self.pot_dist < 40.0 else 0.0)

        feats = np.array([
            1.0,                                      # Bias
            self.pot_dist / 80.0,                     # Normalized distance
            (self.pot_lat - self.veh_lat) / 2.5,      # Relative lateral offset
            self.pot_depth / 20.0,                    # Depth
            self.veh_speed / self.max_speed,          # Speed
            self.pot_water,                           # Waterlogged
            left_dist / self.lane_width,              # Left road margin
            right_dist / self.lane_width,             # Right road margin
            hit_risk * is_near,                       # Collision hazard factor
            float(self.damper_stiff),                 # Damper state
            (self.pot_depth / 20.0) * is_near,        # Near-field severity
            (self.veh_speed / self.max_speed)**2      # Kinetic energy factor
        ], dtype=np.float32)
        return feats

    def step(self, action):
        self.step_count += 1
        dt = 0.1 # 100ms control step
        
        lateral_jerk = 0.0
        if action == 0: pass # Cruise
        elif action == 1: self.veh_speed = max(10.0, self.veh_speed - 14.0 * dt)
        elif action == 2: self.veh_speed = max(0.0, self.veh_speed - 30.0 * dt)
        elif action == 3: self.veh_lat -= 1.8 * dt; lateral_jerk = 0.4
        elif action == 4: self.veh_lat += 1.8 * dt; lateral_jerk = 0.4
        elif action == 5: self.damper_stiff = True

        v_mps = self.veh_speed / 3.6
        self.pot_dist -= v_mps * dt

        reward = 0.08 * (self.veh_speed / self.max_speed) - 0.05 * lateral_jerk
        done = False

        if abs(self.veh_lat) > (self.lane_width / 2.0):
            reward -= 250.0 # Lane departure penalty!
            done = True

        if self.pot_dist <= 0.0:
            done = True
            hit_offset = abs(self.pot_lat - self.veh_lat)
            if hit_offset < 0.65: # Struck pothole!
                damage = self.pot_depth * 12.0
                if self.damper_stiff:
                    damage *= 0.4 # Absorbed 60% of impact
                reward -= (100.0 + damage)
            else: # Evasion bonus
                reward += 120.0

        if self.step_count > 60:
            done = True

        return self._get_features(), reward, done, {}

class PotholeAvoidanceRLAgent:
    """
    Trained Reinforcement Learning Agent for Vehicle Guidance & Suspension Modulation.
    Uses Q-Learning with Linear Function Approximation.
    """
    def __init__(self):
        self.feature_dim = 12
        self.action_dim = 6
        self.W = np.zeros((self.action_dim, self.feature_dim), dtype=np.float32)
        self.gamma = 0.96
        self._load_or_train()

    def _load_or_train(self):
        if os.path.exists(RL_WEIGHTS_PATH):
            try:
                with open(RL_WEIGHTS_PATH, 'r') as f:
                    d = json.load(f)
                    self.W = np.array(d['weights'], dtype=np.float32)
                return
            except Exception:
                pass

        self.train_policy(episodes=600)

    def train_policy(self, episodes=600, lr=0.015):
        print("=" * 72)
        print("      TRAINING REINFORCEMENT LEARNING AGENT (EVASION & SUSPENSION)    ")
        print("=" * 72)
        env = PotholeEvasionEnv()
        epsilon = 0.90
        decay = 0.992
        min_eps = 0.05
        rng = np.random.RandomState(42)

        t0 = time.time()
        for ep in range(episodes):
            s = env.reset()
            total_r = 0.0
            done = False

            while not done:
                # Epsilon-greedy action
                q_vals = np.dot(self.W, s)
                if rng.rand() < epsilon:
                    a = rng.randint(0, self.action_dim)
                else:
                    a = int(np.argmax(q_vals))

                s_next, r, done, _ = env.step(a)
                total_r += r

                # Q-learning TD target
                q_next = np.max(np.dot(self.W, s_next)) if not done else 0.0
                td_error = (r + self.gamma * q_next) - q_vals[a]

                # Update weights
                self.W[a] += lr * td_error * s

                s = s_next

            epsilon = max(min_eps, epsilon * decay)
            if (ep + 1) % 150 == 0:
                print(f"  [RL Episode {ep+1:3d}/{episodes}] Total Reward: {total_r:>6.1f} | Epsilon: {epsilon:.3f}")

        # Save weights
        with open(RL_WEIGHTS_PATH, 'w') as f:
            json.dump({'weights': self.W.tolist(), 'actions': ACTION_NAMES}, f, indent=2)
        print(f"[RL] Policy weights saved to: {RL_WEIGHTS_PATH} in {time.time()-t0:.1f}s")

    def decide_guidance(self, hazard_dict, veh_speed_kmh=35.0):
        """
        Takes active multi-modal hazard and returns RL-recommended vehicle action.
        """
        if not hazard_dict or hazard_dict.get('fused_distance_m', 99) > 65.0:
            return ACTION_GUIDANCE[0][0], ACTION_GUIDANCE[0][1], "CRUISE_MAINTAIN_SPEED"

        dist = float(hazard_dict.get('fused_distance_m', 25.0))
        lat = float(hazard_dict.get('lateral_offset_m', 0.0))
        depth = float(hazard_dict.get('sonar_depth_cm', 8.5))
        water = 1.0 if hazard_dict.get('is_waterlogged', False) else 0.0

        hit_risk = max(0.0, 1.0 - abs(lat) / 0.8)
        is_near = 1.0 if dist < 20.0 else (0.5 if dist < 40.0 else 0.0)

        # 12 basis features
        feats = np.array([
            1.0,
            dist / 80.0,
            lat / 2.5,
            depth / 20.0,
            veh_speed_kmh / 60.0,
            water,
            0.5,
            0.5,
            hit_risk * is_near,
            0.0,
            (depth / 20.0) * is_near,
            (veh_speed_kmh / 60.0)**2
        ], dtype=np.float32)

        q_vals = np.dot(self.W, feats)
        a_idx = int(np.argmax(q_vals))

        action_name = ACTION_NAMES[a_idx]
        text, badge_style = ACTION_GUIDANCE[a_idx]
        return text, badge_style, action_name

    def get_full_decision(self, hazard_dict, veh_speed_kmh=35.0):
        """
        Returns full RL policy evaluation dictionary with Q-values and damper level.
        """
        if not hazard_dict or hazard_dict.get('fused_distance_m', 99) > 65.0:
            return {
                'action_name': 'CRUISE_MAINTAIN_SPEED',
                'guidance_text': 'Maintain cruising speed',
                'badge_style': 'ok',
                'q_value': 1.0,
                'damper_stiffness': 0.20,
                'policy_mode': 'Reinforcement Learning (Q-Policy)'
            }

        dist = float(hazard_dict.get('fused_distance_m', 25.0))
        lat = float(hazard_dict.get('lateral_offset_m', 0.0))
        depth = float(hazard_dict.get('sonar_depth_cm', 8.5))
        water = 1.0 if hazard_dict.get('is_waterlogged', False) else 0.0

        hit_risk = max(0.0, 1.0 - abs(lat) / 0.8)
        is_near = 1.0 if dist < 20.0 else (0.5 if dist < 40.0 else 0.0)

        feats = np.array([
            1.0,
            dist / 80.0,
            lat / 2.5,
            depth / 20.0,
            veh_speed_kmh / 60.0,
            water,
            0.5,
            0.5,
            hit_risk * is_near,
            0.0,
            (depth / 20.0) * is_near,
            (veh_speed_kmh / 60.0)**2
        ], dtype=np.float32)

        q_vals = np.dot(self.W, feats)
        a_idx = int(np.argmax(q_vals))

        damper = 0.25
        if a_idx == 5:
            damper = 0.90 # ACTIVE_DAMPER_STIFFEN
        elif a_idx in (1, 2):
            damper = 0.65
        elif a_idx in (3, 4):
            damper = 0.50

        text, badge_style = ACTION_GUIDANCE[a_idx]
        return {
            'action_name': ACTION_NAMES[a_idx],
            'guidance_text': text,
            'badge_style': badge_style,
            'q_value': round(float(q_vals[a_idx]), 2),
            'damper_stiffness': round(damper, 2),
            'policy_mode': 'Reinforcement Learning (Q-Policy)'
        }

if __name__ == '__main__':
    agent = PotholeAvoidanceRLAgent()

    # Test Case 1: Severe 12cm pothole at 12m ahead in right tire track
    h1 = {'fused_distance_m': 12.0, 'lateral_offset_m': 0.9, 'sonar_depth_cm': 12.5, 'is_waterlogged': True}
    adv1, style1, act1 = agent.decide_guidance(h1, veh_speed_kmh=42.0)
    print(f"\n[RL POLICY TEST 1] Severe Pothole at 12m (Depth 12.5cm, Right Wheel):")
    print(f"  Recommended Action: {act1}")
    print(f"  Driver Guidance:    {adv1} [{style1.upper()}]")

    # Test Case 2: Shallow pothole at 45m ahead
    h2 = {'fused_distance_m': 45.0, 'lateral_offset_m': -0.3, 'sonar_depth_cm': 6.0, 'is_waterlogged': False}
    adv2, style2, act2 = agent.decide_guidance(h2, veh_speed_kmh=35.0)
    print(f"\n[RL POLICY TEST 2] Distant Pothole at 45m (Depth 6.0cm, Center):")
    print(f"  Recommended Action: {act2}")
    print(f"  Driver Guidance:    {adv2} [{style2.upper()}]")
