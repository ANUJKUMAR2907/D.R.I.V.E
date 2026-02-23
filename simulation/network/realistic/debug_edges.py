import os
import sys
import traci

# Ensure traci is available
if 'SUMO_HOME' in os.environ:
    if os.path.join(os.environ['SUMO_HOME'], 'tools') not in sys.path:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

print("Starting SUMO (headless) to inspect network...")
sys.stdout.flush()

try:
    # Use 'sumo' (headless) with --start to ensure immediate execution
    # Use unique stats output to avoid file lock conflict with running controller
    traci.start([
        "sumo", 
        "-c", "city.sumocfg", 
        "--start", 
        "--statistic-output", "stats_debug.xml"
    ])
    
    edges = traci.edge.getIDList()
    
    print(f"Total edges: {len(edges)}")
    print(f"First 20 edges: {edges[:20]}")
    
    traci.close()
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
