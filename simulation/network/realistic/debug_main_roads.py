import os
import sys
import traci

if 'SUMO_HOME' in os.environ:
    if os.path.join(os.environ['SUMO_HOME'], 'tools') not in sys.path:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

print("Starting SUMO (headless) to find major roads...")
try:
    # Use 'sumo' (headless) with unique stats file
    traci.start([
        "sumo", 
        "-c", "city.sumocfg", 
        "--start", 
        "--statistic-output", "stats_debug_lanes.xml"
    ])
    
    important_edges = []
    
    # Iterate through all edges
    for edge in traci.edge.getIDList():
        # Clean up internal edges (starting with ":") if any
        if edge.startswith(":"):
            continue
            
        try:
            lanes = traci.edge.getLaneNumber(edge)
            if lanes >= 3:   # highways / main roads
                important_edges.append(edge)
        except Exception:
            pass

    print(f"Total edges scanned: {len(traci.edge.getIDList())}")
    print(f"Main road edges ({len(important_edges)}):")
    print(important_edges[:20])
    
    traci.close()
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
