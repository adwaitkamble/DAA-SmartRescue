# SmartRescue EMS: Multi-Algorithm Optimization for Emergency Logistics

**Course:** Design and Analysis of Algorithms (DAA) - Mini Project  
**Institution:** Pimpri Chinchwad College of Engineering (PCCOE)  
**Team Members:** * Adwait Kamble (PRN: 123B1D002)
* Aryan Aradhye (PRN: 121B1D058)

---

## 📌 1. Project Overview
SmartRescue EMS is an advanced simulation dashboard designed to solve complex logistics and routing problems within Emergency Medical Services. Moving beyond basic point-to-point dispatching, this system tackles multi-objective optimization: pre-computing city-wide traffic matrices, maximizing the life-saving utility of ambulance payloads, and calculating optimal multi-stop transport routes for critical supplies (blood/organs). 

## 🧠 2. Algorithmic Mapping (DAA Syllabus Integration)
The core logic of this project is strictly derived from the DAA curriculum:

1. **Floyd-Warshall Algorithm (All-Pairs Shortest Path)**
   * **Syllabus:** Unit III - Dynamic Programming Strategy.
   * **Application:** Pre-computes and maintains a matrix of the shortest travel times between all major intersections and hospitals simultaneously, allowing for $O(1)$ dispatch lookups.
2. **0/1 Knapsack**
   * **Syllabus:** Unit III - Dynamic Programming Strategy.
   * **Application:** Optimizes the packing of an ambulance. Given a strict weight capacity, it selects the combination of medical equipment that yields the highest total "life-saving priority value."
3. **Traveling Salesperson Problem (TSP) using Least Cost (LC) Search**
   * **Syllabus:** Unit IV - Branch and Bound Strategy.
   * **Application:** Solves the multi-hospital supply run. A transport vehicle must visit a set of selected hospitals exactly once to drop off blood/organs and return to base, minimizing total travel time.

---

## 📂 3. Folder Structure
The project follows a decoupled architecture, separating the algorithmic engine from the user interface.

├── backend/
│   ├── algorithms.py     (Contains isolated logic for DP and Branch & Bound)
│   ├── app.py            (Handles Flask/FastAPI HTTP requests and responses)
│   └── data.py           (Contains static JSON/dict representations of PCMC map & inventory)
│
├── frontend/
│   ├── index.html        (Main interactive dashboard)
│   ├── css/style.css     (Styling for a dark-mode medical UI)
│   └── js/app.js         (Handles DOM updates and asynchronous API calls)
│
└── README.md             (Project documentation)
