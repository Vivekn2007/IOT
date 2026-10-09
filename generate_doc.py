import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def create_document():
    doc = docx.Document()

    # Page Margins: 1 inch on all sides
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles & Colors
    # Primary: Deep Navy (#1A365D), Secondary: Teal (#0D9488), Accent: Dark Slate (#334155)
    NAVY = RGBColor(26, 54, 93)
    TEAL = RGBColor(13, 148, 136)
    SLATE = RGBColor(51, 65, 85)
    GRAY = RGBColor(100, 116, 139)

    # Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("Advanced Multi-Modal Perception System for Real-Time Pothole Detection in Adverse Weather")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = NAVY

    # Subtitle
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(18)
    run_sub = sub_p.add_run("Comprehensive Engineering Blueprint, Virtual Prototyping Roadmap & 6-Person Work Division")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = TEAL

    # Horizontal Rule
    p_hr = doc.add_paragraph()
    p_hr.paragraph_format.space_after = Pt(14)
    p_hr_border = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="1" w:color="0D9488"/></w:pBdr>')
    p_hr._p.get_or_add_pPr().append(p_hr_border)

    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        run = h.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        run = h.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = TEAL
        return h

    def add_h3(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(3)
        h.paragraph_format.keep_with_next = True
        run = h.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = SLATE
        return h

    def add_p(text, bold_prefix=None, italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            run_b = p.add_run(bold_prefix)
            run_b.font.name = "Calibri"
            run_b.font.size = Pt(10.5)
            run_b.font.bold = True
            run_b.font.color.rgb = SLATE
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.italic = italic
        run.font.color.rgb = SLATE
        return p

    def add_bullet(text, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            run_b = p.add_run(bold_prefix)
            run_b.font.name = "Calibri"
            run_b.font.size = Pt(10.5)
            run_b.font.bold = True
            run_b.font.color.rgb = SLATE
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = SLATE
        return p

    def add_callout(text, title="CRITICAL REQUIREMENT"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "F0FDF4") # soft light green/teal tint
        set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="0D9488"/>
                <w:top w:val="none"/>
                <w:right w:val="none"/>
                <w:bottom w:val="none"/>
            </w:tcBorders>
        ''')
        tcPr.append(borders)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        r_t = p.add_run(f"[{title}] ")
        r_t.font.name = "Calibri"
        r_t.font.size = Pt(10)
        r_t.font.bold = True
        r_t.font.color.rgb = TEAL
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.color.rgb = SLATE
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 1. Executive Summary
    add_h1("1. Executive Summary & Problem Formulation")
    add_p(
        "Road infrastructure integrity directly impacts transportation safety, supply chains, and vehicle longevity. "
        "During intense monsoon periods (such as those across India), rapid road erosion causes widespread pothole generation. "
        "Under adverse environmental conditions—such as torrential rainfall, dense fog, standing water, and road glare—traditional "
        "optical camera-based ADAS systems catastrophically fail because visual cues are obliterated by Mie/Rayleigh particulate "
        "scattering and light refraction through turbid water."
    )
    add_p(
        "To achieve resilient detection, this project operationalizes a multi-modal perception architecture uniting visible-spectrum "
        "computer vision, downward-facing high-frequency acoustic profiling (leveraging AUV sonar mechanics), 77 GHz FMCW millimeter-wave "
        "radar, and chassis shock telemetry. By fusing these streams through 3D Frustum filtering and an adaptive Extended Kalman Filter (EKF), "
        "the edge system achieves sub-5 mm depth accuracy and guaranteed operation under 100 ms per frame latency."
    )

    # 2. Physics of Sub-Surface & Obscured Detection
    add_h1("2. Physics of Sub-Surface & Obscured Perception")
    add_p(
        "The core physical dilemma is detecting a volumetric void submerged beneath a secondary medium (muddy water/debris) "
        "that visually blends with the surrounding asphalt. The success of active wave sensing depends directly on wavelength and medium mechanics:"
    )

    add_bullet(
        "When visible light (400-700 nm) hits waterlogged asphalt, refraction is dictated by Snell's Law: n1*sin(θ1) = n2*sin(θ2). "
        "In turbid, suspended-particulate water, severe Mie and Rayleigh scattering attenuates optical and near-infrared LiDAR rays, "
        "causing complete signal extinction or noisy, unusable point clouds.",
        bold_prefix="Optical & LiDAR Degradation: "
    )
    add_bullet(
        "Inspired by IIT Bombay's Matsya Autonomous Underwater Vehicles (AUVs), mechanical acoustic waves (25 kHz to 50 kHz) propagate "
        "readily through turbid liquids regardless of optical clarity. At acoustic impedance boundaries (Z = ρ * c), partial reflection "
        "occurs at the air-water interface and the asphalt floor. Time-of-Flight (ToF) depth calculation D = (v * t) / 2 "
        "(with v ≈ 343 m/s in air and v ≈ 1,480 m/s in water) decouples the water surface from true pothole bed depth.",
        bold_prefix="Acoustic Sonar Mechanics: "
    )
    add_bullet(
        "Forward-looking detection up to 150 meters is achieved using 77-81 GHz FMCW radar (wavelength λ ≈ 3.9 mm). "
        "Because water possesses an exceptionally high relative permittivity (ε_r ≈ 80) compared to dry asphalt (ε_r ≈ 4), "
        "waterlogged potholes exhibit a drastic +20 dB Radar Cross Section (RCS) anomaly, appearing as intensely bright markers "
        "in radar point clouds even through heavy fog.",
        bold_prefix="77 GHz mmWave FMCW Radar: "
    )

    # Table for Dielectric constants
    tbl_d = doc.add_table(rows=5, cols=4)
    tbl_d.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Material", "Dielectric Constant (ε_r)", "Conductivity (σ, S/m)", "RCS Radar Backscatter Impact"]
    for i, h in enumerate(headers):
        cell = tbl_d.cell(0, i)
        set_cell_background(cell, "1A365D")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    data_d = [
        ["Dry Asphalt", "4.0", "0.006", "Low baseline backscatter; partially absorbs mmWave energy."],
        ["Dry Concrete", "10.0", "0.006", "Moderate baseline backscatter."],
        ["Air (Empty Pothole)", "1.0", "0.0", "Geometric edge diffraction produces slight return variance."],
        ["Rainwater / Mud", "4.3 to 80.0", "0.003", "Massive contrast; reflects strongly (+20 dB RCS spike)."]
    ]
    for r_idx, row_data in enumerate(data_d):
        for c_idx, val in enumerate(row_data):
            cell = tbl_d.cell(r_idx + 1, c_idx)
            if r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            if c_idx in [1, 2]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(val)
            run.font.name = "Calibri"
            run.font.size = Pt(9)
            run.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # 3. Virtual Assembly & Prototyping Environment
    add_h1("3. Virtual Assembly & Digital Twin Simulation")
    add_p(
        "Deploying uncalibrated perception stacks directly onto physical test vehicles during active monsoons introduces unacceptable "
        "safety and hardware destruction risks. Therefore, the entire system must first be assembled and verified within a high-fidelity "
        "digital twin."
    )
    add_callout(
        "The primary development environment is CARLA Simulator (0.9.14+) running with the native ROS 2 Bridge. "
        "Virtual sensor topics must exactly mirror physical sensor topics so that nodes can be deployed to the physical "
        "NVIDIA Jetson edge processor without rewriting a single line of application code.",
        title="SIM-TO-REAL PARADIGM"
    )

    add_h2("Sensor Mounting Geometry in CARLA")
    add_bullet("Placed at the central front bumper/grille (height: 0.4 m - 0.6 m). Modeled with ray-casting FMCW emulation producing Range-Doppler point clouds up to 150 meters.", bold_prefix="77 GHz FMCW Radar: ")
    add_bullet("Mounted behind the windshield / rearview mirror assembly (height: 1.3 m, looking forward). Configured for 720p/1080p resolution at 30 FPS.", bold_prefix="Optical RGB Camera: ")
    add_bullet("Under-chassis mounting directed strictly orthogonal to the road surface (height: 0.3 m - 0.5 m baseline road clearance). Emulated via high-dispersion ray-casts reflecting ToF in air and standing water.", bold_prefix="Downward Ultrasonic Array: ")
    add_bullet("Mounted rigidly at the vehicle chassis center of mass to capture vertical (Z-axis) shock accelerations during wheel-impact events.", bold_prefix="6-Axis IMU (MPU6050): ")

    add_h2("Dynamic Environmental Simulation")
    add_bullet("Rainfall intensity parameter swept from 0.0 to 1.0 (heavy monsoon).", bold_prefix="Precipitation: ")
    add_bullet("Road puddle deposition parameter set to 1.0 to generate standing turbid water in road depressions.", bold_prefix="Puddles & Standing Water: ")
    add_bullet("Atmospheric fog density parameter set to 0.70 - 0.90 to stress optical camera boundaries.", bold_prefix="Fog & Mist: ")

    # 4. The First Step
    add_h1("4. The Absolute First Step in Project Execution")
    add_p(
        "The project must NOT begin with isolated machine learning training or independent microcontroller code. "
        "The foundational first step is to establish the unified virtual communication backbone:"
    )
    add_bullet("Step 1: Install ROS 2 Humble (Ubuntu 22.04 LTS or WSL2) and CARLA Simulator 0.9.14+.")
    add_bullet("Step 2: Launch an ego-vehicle equipped with camera, radar, downward ray-cast ultrasonic, and IMU blueprints.")
    add_bullet("Step 3: Verify the ROS 2 Bridge is streaming standard messages: /sensors/camera/image_raw (sensor_msgs/Image), /sensors/radar/points (sensor_msgs/PointCloud2), /sensors/ultrasonic/range (sensor_msgs/Range), and /sensors/imu/data (sensor_msgs/Imu).")
    add_bullet("Step 4: Create a synthetic test road containing an empty pothole and a waterlogged pothole, confirming that all 4 topics register variance as the car approaches.")
    add_p("Once this virtual test harness is active, all 6 team members can build and test their specialized modules concurrently against real-time simulated streams.")

    # 5. Work Division Across 6 People
    add_h1("5. Comprehensive Work Division Across 6 Team Members")
    add_p(
        "The entire scope of the project—from mathematical modeling and synthetic simulation to deep learning, sensor fusion, "
        "and physical embedded hardware—is divided among 6 distinct roles. Each person owns their module entirely."
    )

    team_roles = [
        {
            "id": "Person 1",
            "title": "Simulation Architect & System Integration Engineer",
            "scope": "CARLA digital twin environment, vehicle sensor mounting, ROS 2 middleware architecture, and end-to-end integration.",
            "tasks": [
                "Construct and maintain the CARLA simulation environment with realistic Indian road meshes (ASAM OpenDRIVE/OpenSCENARIO), potholes, and variable puddle depths.",
                "Program dynamic monsoon weather states: torrential rain, road standing water, atmospheric fog, and low-angle sun glare.",
                "Mount virtual sensors (camera, radar, downward ultrasonic, IMU) onto the vehicle rig with precise 6-DOF geometric transforms (TF2).",
                "Configure and maintain the carla_ros_bridge, unified ROS 2 package workspace (colcon), custom .msg definitions, and master system launch files (system_bringup.launch.py).",
                "Orchestrate system-wide regression tests and latency benchmarks across all connected sub-nodes."
            ],
            "in_out": "Inputs: Algorithm nodes from Persons 2-6. Outputs: Master simulation environment, raw sensor topics (/sensors/*), and system launch scripts.",
            "deliverables": "CARLA monsoon road environment, TF2 vehicle coordinate tree, pothole_simulation_bringup ROS 2 package, and system CI/CD pipeline."
        },
        {
            "id": "Person 2",
            "title": "Computer Vision & Deep Learning Specialist",
            "scope": "Daylight optical defect detection, dataset engineering, adverse weather data augmentation, and CNN inference.",
            "tasks": [
                "Extract and clean the India-specific road damage subset from the RDD2022 dataset (3,187 D40 pothole annotations in Pascal VOC format).",
                "Integrate the N-RDD2024 10-class taxonomy to discriminate between potholes (D40) and false positives: manholes (D70), patches (D80), and alligator cracks (D20).",
                "Develop the adverse weather augmentation pipeline: Perlin noise overlays (fog), synthetic rain streaks, and localized water surface glare filters.",
                "Implement optical preprocessing: CLAHE (Contrast Limited Adaptive Histogram Equalization) for harsh shadows, and Bilateral Filtering for edge-preserving asphalt smoothing.",
                "Train and benchmark real-time models: YOLOv8 (with DSConv depthwise separable convolutions and SimAM attention), POT-YOLO, DPD-Net, and Mask R-CNN.",
                "Package the trained detector into an optimized ROS 2 node publishing 2D bounding boxes and classification confidences."
            ],
            "in_out": "Inputs: /sensors/camera/image_raw from Person 1 (or real camera). Outputs: /perception/vision/detections_2d to Person 5.",
            "deliverables": "Trained YOLOv8 / DPD-Net model weights (.pt and .onnx), weather augmentation pipeline, and pothole_vision_node ROS 2 package."
        },
        {
            "id": "Person 3",
            "title": "mmWave Radar & RF Signal Processing Engineer",
            "scope": "77 GHz FMCW radar signal processing, SFCC algorithm, RCS anomaly extraction, and TI hardware interface.",
            "tasks": [
                "Model electromagnetic scattering physics: exploit the dielectric constant contrast between asphalt (ε_r ≈ 4) and muddy water (ε_r ≈ 80) to detect the characteristic +20 dB RCS anomaly.",
                "Implement the FMCW radar chirp parameterization (fc = 77 GHz, bandwidth B, duration Tc) and process Intermediate Frequency (IF) beat frequencies.",
                "Develop the Stepped Frequency Continuous Wave / Cross-Correlation (SFCC) algorithm across multi-channel receiving antennas to eliminate multipath reflections, phase noise, and road clutter, achieving sub-5 mm depth precision.",
                "Interface the physical Texas Instruments IWR1443BOOST radar and DCA1000EVM capture board; parse high-speed UDP streams (700 Mbps Gigabit Ethernet) to reassemble raw 16-bit ADC samples across 4 RX antennas.",
                "Build the ROS 2 Radar Node to output clean 3D radar point clouds with range, azimuth, Doppler velocity, and RCS intensity attributes."
            ],
            "in_out": "Inputs: Simulated radar points from Person 1 / raw DCA1000EVM UDP stream. Outputs: /perception/radar/targets_3d to Person 5.",
            "deliverables": "SFCC signal processing C++/Python library, TI IWR1443 driver & UDP packet parser, and pothole_radar_dsp ROS 2 package."
        },
        {
            "id": "Person 4",
            "title": "Acoustic Profiling & Mechanical Telemetry Engineer",
            "scope": "Turbid water volumetric depth sensing (AUV Matsya sonar logic) and chassis shock impact confirmation.",
            "tasks": [
                "Formulate acoustic Time-of-Flight (ToF) equations across impedance boundaries (Z = ρ * c) using 25 kHz - 50 kHz downward-facing ultrasonic transceivers.",
                "Implement dual-echo separation algorithms to distinguish the air-water reflection from the true submerged pothole asphalt floor (compensating for v_air ≈ 343 m/s vs. v_water ≈ 1,480 m/s).",
                "Continuously track baseline road clearance distance (D_normal) to calculate true pothole depth: Depth = D_pothole - D_normal.",
                "Incorporate Doppler shift compensation to ensure distance accuracy under vehicle motion at varying cruising speeds.",
                "Interface the MPU6050 6-axis IMU on the vehicle chassis/suspension; build an adaptive threshold filter on vertical acceleration (Z-axis shock) as a fail-safe ground-truth confirmation when a pothole is struck.",
                "Build the ROS 2 node streaming calibrated ultrasonic depth measurements and IMU shock warnings."
            ],
            "in_out": "Inputs: Downward ultrasonic echo waveforms and IMU I2C/SPI telemetry. Outputs: /perception/acoustic/depth_profile and /sensors/imu/chassis_shock to Persons 5 and 6.",
            "deliverables": "Dual-media acoustic ToF solver, MPU6050 suspension spike detection filter, and pothole_acoustic_imu ROS 2 package."
        },
        {
            "id": "Person 5",
            "title": "Sensor Fusion & 3D Spatial Geometry Engineer",
            "scope": "3D Frustum RoI generation, probabilistic state estimation, and adaptive Extended Kalman Filter (EKF).",
            "tasks": [
                "Implement 3D Frustum RoI Extraction: project 2D bounding boxes from the vision model (Person 2) into 3D viewing cones using camera intrinsic calibration matrices [fx, fy, cx, cy].",
                "Gate and isolate mmWave radar points (Person 3) and acoustic readings (Person 4) inside the 3D frustum, discarding extraneous road data to achieve an 88.2% reduction in computation.",
                "Build the Extended Kalman Filter (EKF): Kinematic prediction step based on vehicle velocity, steering angle, and IMU yaw rate to project pothole relative positions.",
                "Develop the EKF Update/Correction step using adaptive inverse-covariance weighting: z_hat = Σ(Ri^-1 * yi) / Σ(Ri^-1).",
                "Implement Graceful Degradation logic: dynamically expand the vision covariance matrix during fog or water glare, automatically down-weighting optical inputs and shifting reliance to 77 GHz radar and ultrasonic sonar.",
                "Publish unified 3D obstacle state vectors containing exact distance, lateral position, depth, volume, and hazard severity classification."
            ],
            "in_out": "Inputs: Detections from Person 2 (Vision), Person 3 (Radar), and Person 4 (Acoustics/IMU). Outputs: /fusion/pothole_tracks (3D state vectors) to Person 6.",
            "deliverables": "3D Frustum point-cloud spatial gating node, adaptive inverse-covariance EKF filter, and pothole_sensor_fusion ROS 2 package."
        },
        {
            "id": "Person 6",
            "title": "Edge Computing, Driver HMI & Cloud IoT Engineer",
            "scope": "NVIDIA Jetson TensorRT runtime optimization, in-cabin TFT LCD driver GUI, audio alarm, and municipal NB-IoT telemetry.",
            "tasks": [
                "Containerize and optimize the full ROS 2 perception stack on the NVIDIA Jetson Orin Nano / BM3823A edge platform.",
                "Convert and quantize Person 2's vision models into TensorRT (FP16/INT8 engines) to enforce real-time inference within the strict 100 ms/frame deadline.",
                "Develop a high-visibility in-cabin driver Graphical User Interface (GUI) for a TFT LCD screen using Qt/PyQt or lightweight C++ SDL.",
                "Render augmented depth maps, color-coded severity warnings (yellow/red), distance countdowns, and proactive deceleration prompts on the driver display.",
                "Drive hardware GPIO pins to trigger an active audible warning buzzer when hazardous submerged potholes are detected ahead.",
                "Interface the MZH010 NB-IoT wireless module via UART/AT commands; implement MQTT/HTTPS payloads transmitting GPS coordinates, depth, width, timestamp, and severity to municipal cloud servers."
            ],
            "in_out": "Inputs: /fusion/pothole_tracks from Person 5; chassis shock hits from Person 4. Outputs: TFT LCD driver HUD, audio buzzer GPIO triggers, and NB-IoT cloud telemetry packets.",
            "deliverables": "TensorRT Jetson deployment runtime container, in-cabin driver GUI & buzzer controller, and pothole_telemetry_node ROS 2 package."
        }
    ]

    for member in team_roles:
        add_h2(f"{member['id']}: {member['title']}")
        add_p(member['scope'], bold_prefix="Primary Domain & Scope: ")
        add_p("Core Technical Responsibilities:", bold_prefix=None, italic=True)
        for t in member['tasks']:
            add_bullet(t)
        add_p(member['in_out'], bold_prefix="Interface Boundaries: ")
        add_p(member['deliverables'], bold_prefix="Key Deliverables: ")
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 6. Inter-Team Data Flow & Dependency Architecture
    add_h1("6. Inter-Team Data Flow & System Topology")
    add_p(
        "To eliminate development bottlenecks, all members communicate through strict, predefined ROS 2 interfaces. "
        "The complete architecture functions as follows:"
    )

    data_flows = [
        ["1. Simulation / Hardware", "Person 1", "Raw Camera Frames (/sensors/camera/image_raw)", "Person 2 (Vision)"],
        ["2. Simulation / Hardware", "Person 1", "Raw mmWave Radar Stream (/sensors/radar/points)", "Person 3 (Radar)"],
        ["3. Simulation / Hardware", "Person 1", "Ultrasonic Echoes & IMU Data (/sensors/ultrasonic/range, /imu)", "Person 4 (Acoustics/IMU)"],
        ["4. Vision Processing", "Person 2", "2D Bounding Boxes & Confidence (/perception/vision/detections_2d)", "Person 5 (Fusion)"],
        ["5. Radar Processing", "Person 3", "Filtered 3D Radar Points & RCS (/perception/radar/targets_3d)", "Person 5 (Fusion)"],
        ["6. Acoustic & IMU", "Person 4", "Submerged Depth Profiles & Shock Alerts", "Person 5 (Fusion) & Person 6 (IoT)"],
        ["7. Sensor Fusion", "Person 5", "Unified 3D Hazard State Vectors (/fusion/pothole_tracks)", "Person 6 (HMI & IoT)"],
        ["8. Driver HMI & Cloud", "Person 6", "TFT LCD HUD, Audio Buzzer, and NB-IoT Municipal Cloud Telemetry", "End Drivers & Road Authorities"]
    ]

    tbl_f = doc.add_table(rows=len(data_flows) + 1, cols=4)
    tbl_f.alignment = WD_TABLE_ALIGNMENT.CENTER
    f_headers = ["Pipeline Stage", "Producer", "Data Payload / Topic", "Consumer"]
    for i, h in enumerate(f_headers):
        cell = tbl_f.cell(0, i)
        set_cell_background(cell, "1A365D")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, row_data in enumerate(data_flows):
        for c_idx, val in enumerate(row_data):
            cell = tbl_f.cell(r_idx + 1, c_idx)
            if r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            run = p.add_run(val)
            run.font.name = "Calibri"
            run.font.size = Pt(9)
            run.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # 7. Hardware Bill of Materials (BOM) & Edge Specs
    add_h1("7. Physical Hardware Bill of Materials (BOM)")
    add_p("When transitioning from the CARLA digital twin to the physical in-vehicle prototype, the following hardware components are utilized:")

    bom_data = [
        ["Main Edge Processor", "NVIDIA Jetson Orin Nano / BM3823A", "Executes TensorRT YOLOv8, SFCC radar algorithms, and EKF fusion within 100 ms."],
        ["mmWave Radar Module", "Texas Instruments IWR1443BOOST", "76-81 GHz FMCW radar with integrated DSP; provides forward-looking range up to 150 m."],
        ["Radar Data Acquisition", "TI DCA1000EVM", "Captures raw radar IF ADC samples and streams via Gigabit Ethernet UDP at 700 Mbps."],
        ["Acoustic Transceivers", "Industrial Waterproof Ultrasonic Array (25-50 kHz)", "Under-chassis downward ToF sounding for submerged pothole depth measurement."],
        ["Fail-Safe Motion Sensor", "MPU6050 6-Axis IMU", "Measures chassis vertical Z-axis shock to register ground-truth pothole encounters."],
        ["Driver Display", "7-inch High-Brightness TFT LCD Screen", "Renders in-cabin driver warnings, augmented depth maps, and deceleration prompts."],
        ["Audible Warning", "Active 5V / 12V Piezoelectric Buzzer", "Triggered via Jetson GPIO for instantaneous driver hazard alerts."],
        ["IoT Cellular Module", "MZH010 NB-IoT Module + GPS", "Uploads geolocated pothole coordinates and severity ratings to municipal cloud servers."]
    ]

    tbl_b = doc.add_table(rows=len(bom_data) + 1, cols=3)
    tbl_b.alignment = WD_TABLE_ALIGNMENT.CENTER
    b_headers = ["Subsystem", "Component Specification", "Primary Operational Function"]
    for i, h in enumerate(b_headers):
        cell = tbl_b.cell(0, i)
        set_cell_background(cell, "1A365D")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.font.name = "Calibri"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, row_data in enumerate(bom_data):
        for c_idx, val in enumerate(row_data):
            cell = tbl_b.cell(r_idx + 1, c_idx)
            if r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            run = p.add_run(val)
            run.font.name = "Calibri"
            run.font.size = Pt(9)
            run.font.color.rgb = SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # 8. Conclusion & Sign-Off
    add_h1("8. Verification & Operational Readiness")
    add_p(
        "By structuring the project around strict module ownership and standardized ROS 2 communication, each team member "
        "develops their subsystem independently without blocking peers. The CARLA simulation environment provides immediate, "
        "deterministic feedback across monsoon weather edge cases. Once the fusion pipeline satisfies the < 100 ms real-time latency "
        "and sub-5 mm depth precision in simulation, the exact same ROS 2 codebase transitions directly onto the physical NVIDIA Jetson "
        "vehicle rig."
    )

    output_path = r"E:\IOT project\Advanced_Pothole_Detection_System_Blueprint.docx"
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == "__main__":
    create_document()
