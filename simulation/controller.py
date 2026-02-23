
import os
import sys
import traci
import sqlite3
import argparse
from datetime import datetime

# --- Constants ---
EDGE_THRESHOLD = 30
LOW_SPEED = 8.3   # 30 km/h
NORMAL_SPEED = 13.9  # 50 km/h
DB_PATH = "simulation_logs.db"
DEFAULT_CONFIG = "network/realistic/city.sumocfg"

# Ensure SUMO_HOME is set
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("Please set SUMO_HOME environment variable")


class TrafficController:
    def __init__(self, config_path):
        self.config_path = config_path
        self.main_edges = []
        self.controlled_tls = []
        self.step = 0
        self.conn = None
        self.cursor = None

    def start_simulation(self):
        """STEP 1: Launch SUMO safely"""
        # Headless mode: using "sumo" instead of "sumo-gui"
        sumo_cmd = ["sumo", "-c", self.config_path, "--start"]
        print(f"Starting SUMO (headless) with: {self.config_path}")
        try:
            traci.start(sumo_cmd)
            print("Connected to TraCI.")
        except Exception as e:
            sys.exit(f"Failed to start SUMO: {e}")

    def setup_database(self):
        """Prepare logging database"""
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicle_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                edge_id TEXT,
                vehicle_count INTEGER
            )
        ''')
        self.conn.commit()

    def inspect_network(self):
        """STEP 2: Inspect existing network"""
        all_edges = traci.edge.getIDList()
        self.main_edges = []
        
        for edge in all_edges:
            if edge.startswith(":"):  # Filter internal edges
                continue
            
            try:
                lanes = traci.edge.getLaneNumber(edge)
                if lanes >= 3:
                    self.main_edges.append(edge)
            except:
                pass

        print(f"Total edges: {len(all_edges)}")
        print(f"Main road edges (>= 3 lanes): {len(self.main_edges)}")

    def identify_traffic_lights(self):
        """STEP 3: Identify traffic lights relevant to main roads"""
        tls_set = set()
        for edge in self.main_edges:
            # Get traffic lights controlling this edge
            # getTLSID returns a list even if there's only one
            tls_list = traci.edge.getTLSID(edge)
            for tls in tls_list:
                tls_set.add(tls)
        
        self.controlled_tls = list(tls_set)
        print(f"Selected traffic lights: {len(self.controlled_tls)}")

    def control_loop(self):
        """Main control loop (Steps 4, 5, 6, 7)"""
        print("Starting control loop...")
        
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            self.step += 1
            
            current_time = datetime.now().isoformat()
            
            # --- STEP 4: Dynamic Speed Limit Control ---
            for edge in self.main_edges:
                try:
                    veh_count = traci.edge.getLastStepVehicleNumber(edge)
                    
                    if veh_count > EDGE_THRESHOLD:
                        traci.edge.setMaxSpeed(edge, LOW_SPEED)
                    else:
                        traci.edge.setMaxSpeed(edge, NORMAL_SPEED)
                    
                    # --- STEP 6: Logging for Proof ---
                    # Only log data for main_edges
                    self.cursor.execute(
                        "INSERT INTO vehicle_logs (timestamp, edge_id, vehicle_count) VALUES (?, ?, ?)",
                        (current_time, edge, veh_count)
                    )
                except Exception:
                    continue  # Skip if edge query fails
            
            # --- STEP 5: Emergency Vehicle Handling ---
            self.handle_emergency_vehicles()
            
            # Commit logs periodically
            if self.step % 100 == 0:
                self.conn.commit()

    def handle_emergency_vehicles(self):
        """Detect and prioritize emergency vehicles"""
        vehicle_ids = traci.vehicle.getIDList()
        
        for vid in vehicle_ids:
            try:
                vclass = traci.vehicle.getVehicleClass(vid)
                if vclass == "emergency":
                    # Function to find upcoming traffic lights logic
                    # Simplified: Get current lane -> next TLS
                    lane_id = traci.vehicle.getLaneID(vid)
                    if not lane_id:
                         continue
                         
                    # Get next traffic light on route
                    next_tls = traci.vehicle.getNextTLS(vid)
                    
                    for tls_entry in next_tls:
                        tls_id = tls_entry[0]
                        # Force green phase (Index 0 is typically Green for main direction, but variable)
                        # Caution: simplified assumption that phase 0 is Green for this approach
                        traci.trafficlight.setPhase(tls_id, 0)
            except Exception:
                pass

    def cleanup(self):
        """STEP 8: Clean Exit"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
        
        traci.close()
        print("\n--- Simulation Summary ---")
        print(f"Total simulation steps: {self.step}")
        print(f"Main edges controlled: {len(self.main_edges)}")
        print(f"Traffic lights overridden (scope): {len(self.controlled_tls)}")
        print("Simulation ended safely.")


def main():
    parser = argparse.ArgumentParser(description="SUMO Traffic Controller")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to .sumocfg")
    # Ignored args to compatible with possible legacy calls, but strict logic internally
    parser.add_argument("--gui", action="store_true", help="Ignored (Always Headless)")
    args = parser.parse_args()

    # Verify config exists
    if not os.path.exists(args.config):
        # Fallback check
        if os.path.exists("city.sumocfg"):
            args.config = "city.sumocfg"
        elif os.path.exists("network/realistic/city.sumocfg"):
            args.config = "network/realistic/city.sumocfg"
        else:
            sys.exit(f"Config file not found: {args.config}")

    controller = TrafficController(args.config)
    controller.setup_database()
    controller.start_simulation()
    
    try:
        controller.inspect_network()
        controller.identify_traffic_lights()
        controller.control_loop()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Runtime error: {e}")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()
