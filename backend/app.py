"""
SmartRescue EMS - Flask API Server
====================================
Serves as the HTTP API layer for the SmartRescue EMS dashboard.
Exposes algorithm endpoints for Floyd-Warshall, 0/1 Knapsack, and TSP.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import copy

from data import city_graph, inventory_db, LOCATIONS, INF
from algorithms import (
    compute_city_routes,
    reconstruct_path,
    optimize_ambulance_loadout,
    plan_multi_stop_route,
)

# --- App Initialization ---
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin requests so the frontend can call the API


# ═══════════════════════════════════════════════════════════════
#  Health Check / Root Endpoint
# ═══════════════════════════════════════════════════════════════

@app.route("/", methods=["GET"])
def index():
    """Returns a welcome message confirming the API is live."""
    return jsonify({
        "status": "online",
        "project": "SmartRescue EMS",
        "message": "API is running. All systems operational."
    })


# ═══════════════════════════════════════════════════════════════
#  Data Endpoints (GET)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/locations", methods=["GET"])
def get_locations():
    """Returns the list of PCMC location names."""
    return jsonify({"locations": LOCATIONS})


@app.route("/api/graph", methods=["GET"])
def get_graph():
    """Returns the raw city adjacency matrix."""
    serializable_graph = [
        [-1 if val == INF else val for val in row]
        for row in city_graph
    ]
    return jsonify({"graph": serializable_graph, "locations": LOCATIONS})


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    """Returns the list of available medical equipment."""
    return jsonify({"inventory": inventory_db})


# ═══════════════════════════════════════════════════════════════
#  Algorithm Endpoints (POST)
# ═══════════════════════════════════════════════════════════════

# --- 1. Floyd-Warshall: All-Pairs Shortest Path ---
@app.route("/api/matrix", methods=["POST"])
def floyd_warshall_endpoint():
    """
    POST /api/matrix
    Runs Floyd-Warshall on the city graph and returns the optimized
    distance matrix along with location labels.
    """
    try:
        dist, next_node = compute_city_routes(city_graph)

        # Replace INF with -1 for clean JSON serialization
        serializable_dist = [
            [-1 if val == INF else val for val in row]
            for row in dist
        ]

        # Build path info for every pair
        paths = {}
        for i in range(len(LOCATIONS)):
            for j in range(len(LOCATIONS)):
                if i != j:
                    path_indices = reconstruct_path(next_node, i, j)
                    path_names = [LOCATIONS[p] for p in path_indices]
                    key = f"{LOCATIONS[i]} → {LOCATIONS[j]}"
                    paths[key] = {
                        "path": path_names,
                        "time": dist[i][j] if dist[i][j] != INF else -1
                    }

        return jsonify({
            "status": "success",
            "algorithm": "Floyd-Warshall (All-Pairs Shortest Path)",
            "complexity": "O(V³)",
            "locations": LOCATIONS,
            "optimized_matrix": serializable_dist,
            "paths": paths
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Floyd-Warshall computation failed: {str(e)}"
        }), 500


# --- 2. 0/1 Knapsack: Ambulance Loadout Optimizer ---
@app.route("/api/knapsack", methods=["POST"])
def knapsack_endpoint():
    """
    POST /api/knapsack
    Expects JSON: { "capacity": <int> }
    Runs 0/1 Knapsack and returns the optimal loadout.
    """
    try:
        data = request.get_json()

        if not data or "capacity" not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required field: 'capacity' (integer, kg)"
            }), 400

        capacity = int(data["capacity"])

        if capacity <= 0:
            return jsonify({
                "status": "error",
                "message": "Capacity must be a positive integer."
            }), 400

        max_value, selected_items = optimize_ambulance_loadout(capacity, inventory_db)
        total_weight = sum(item["weight"] for item in selected_items)

        return jsonify({
            "status": "success",
            "algorithm": "0/1 Knapsack (Dynamic Programming)",
            "complexity": "O(n × W)",
            "capacity": capacity,
            "max_value": max_value,
            "total_weight": total_weight,
            "items_selected": selected_items,
            "items_count": len(selected_items),
            "all_items": inventory_db
        })

    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid capacity value. Must be an integer."
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Knapsack computation failed: {str(e)}"
        }), 500


# --- 3. TSP: Multi-Stop Route Planner (Branch & Bound) ---
@app.route("/api/tsp", methods=["POST"])
def tsp_endpoint():
    """
    POST /api/tsp
    Expects optional JSON: { "overrides": [{"u": int, "v": int, "time": float}, ...] }
    Runs Branch & Bound TSP on the city graph and returns the
    optimal multi-stop route and total travel time.
    """
    try:
        data = request.get_json(silent=True) or {}
        overrides = data.get("overrides", [])
        
        # Deep copy so we don't permanently alter the static matrix
        dynamic_graph = copy.deepcopy(city_graph)
        
        for ov in overrides:
            u, v, time = ov.get("u"), ov.get("v"), ov.get("time")
            if u is not None and v is not None and time is not None:
                # Assuming undirected graph, traffic affects both directions equally
                dynamic_graph[u][v] = time
                dynamic_graph[v][u] = time

        best_path, best_cost = plan_multi_stop_route(dynamic_graph)

        if not best_path:
            return jsonify({
                "status": "success",
                "algorithm": "TSP — Branch & Bound (LC Search)",
                "message": "No valid Hamiltonian cycle found for the given graph.",
                "route": [],
                "route_names": [],
                "total_time": -1
            })

        route_names = [LOCATIONS[i] for i in best_path]

        # Build leg-by-leg breakdown using the dynamic graph
        legs = []
        for k in range(len(best_path) - 1):
            src = best_path[k]
            dst = best_path[k + 1]
            time_cost = dynamic_graph[src][dst]
            legs.append({
                "from": LOCATIONS[src],
                "to": LOCATIONS[dst],
                "time": time_cost if time_cost != INF else -1
            })

        return jsonify({
            "status": "success",
            "algorithm": "TSP — Branch & Bound (LC Search)",
            "complexity": "O(n² × 2ⁿ) worst-case, pruned via lower bounds",
            "route": best_path,
            "route_names": route_names,
            "total_time": best_cost,
            "legs": legs,
            "cities_visited": len(best_path) - 1  # excludes return to start
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"TSP computation failed: {str(e)}"
        }), 500


# ═══════════════════════════════════════════════════════════════
#  Server Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 50)
    print("  SmartRescue EMS API Server")
    print("  http://127.0.0.1:5000")
    print("=" * 50)
    print("\n  Endpoints:")
    print("  GET  /                → Health check")
    print("  GET  /api/locations   → Location list")
    print("  GET  /api/graph       → Raw adjacency matrix")
    print("  GET  /api/inventory   → Medical equipment list")
    print("  POST /api/matrix      → Floyd-Warshall result")
    print("  POST /api/knapsack    → Knapsack optimization")
    print("  POST /api/tsp         → TSP optimal route\n")
    app.run(debug=True, port=5000)
