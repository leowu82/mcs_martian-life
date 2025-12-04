from config import MCSimConfig
from simulation import MarsColony

# ==========================================
# MONTE CARLO SIMULATION
# ==========================================

def run_mcs(experiment_mode, n_simulations=1000):
    print(f"\n--- Starting Experiment: {experiment_mode} ---")
    success_count = 0
    death_reasons = {}
    
    cfg = MCSimConfig(experiment_mode)
    
    for _ in range(n_simulations):
        colony = MarsColony(cfg)
        survived, cause, _ = colony.run_mission()
        
        if survived:
            success_count += 1
        else:
            death_reasons[cause] = death_reasons.get(cause, 0) + 1
            
    success_rate = (success_count / n_simulations) * 100
    print(f"Simulations: {n_simulations}")
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Failure Causes: {death_reasons}")
    return success_rate


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    # Number of simulations per experiment
    n_simulations = 1000
    
    # Run Control
    run_mcs("CONTROL", n_simulations=n_simulations)
    
    # Run Hypothesis 1 (Oxygenator Redundancy)
    run_mcs("OXYGENATOR_REDUNDANCY_TEST", n_simulations=n_simulations)
    
    # Run Hypothesis 2 (Battery Buffer)
    run_mcs("BATTERY_TEST", n_simulations=n_simulations)
    