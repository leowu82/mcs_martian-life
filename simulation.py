from config import MISSION_DURATION, CREW_SIZE
from models import Machine, CropModule, MarsEnvironment

# ==========================================
# CORE SIMULATION LOGIC
# ==========================================

class MarsColony:
    def __init__(self, config):
        self.cfg = config
        self.day = 0
        self.alive = True
        self.cause_of_death = ""
        
        # Resources
        self.o2 = self.cfg.starting_o2
        self.water = self.cfg.starting_water
        self.waste_water = 0.0
        self.battery = self.cfg.starting_battery
        self.food = self.cfg.starting_food
        
        # Systems
        self.env = MarsEnvironment()
        self.crops = CropModule(self.cfg.crop_food_production, self.cfg.crop_o2_production)
        
        # Oxygenators
        self.oxygenators = [
            Machine(f"Oxy-{i}", self.cfg.o2_production_rate, self.cfg.oxygenator_mtbf)
            for i in range(self.cfg.num_oxygenators)
        ]

        # Water Reclaimers
        self.water_reclaimers = [
            Machine(f"WaterRec-{i}", self.cfg.water_reclamation_rate, self.cfg.water_reclaimer_mtbf)
            for i in range(self.cfg.num_water_reclaimers)
        ]

    def step(self):
        """Simulates one day"""
        self.day += 1
        
        # --- 1. Environment & Power Generation ---
        sun_eff = self.env.get_sunlight_efficiency((self.day % 360))
        power_gen = self.cfg.solar_capacity * sun_eff * 8 # kWh per day (8 hours of effective sunlight)
        
        # --- 2. Base Consumption ---
        total_power_need = self.cfg.daily_base_power_consumption
        available_power = self.battery + power_gen - total_power_need
        total_o2_need = self.cfg.daily_o2_consumption * CREW_SIZE
        total_water_need = self.cfg.daily_water_consumption * CREW_SIZE
        total_food_need = self.cfg.daily_food_consumption * CREW_SIZE

        # --- 3. Crop Production ---
        crop_water_available = False
        if self.water >= total_water_need + self.cfg.crop_daily_water_need:
            total_water_need += self.cfg.crop_daily_water_need
            crop_water_available = True
        
        food_produced, crop_o2_produced = self.crops.grow(crop_water_available)

        # --- 4. Waste Water ---
        # Waste water from crew consumption and crop transpiration
        self.waste_water += total_water_need * self.cfg.water_recycle_efficiency
        
        # --- 5. Machine Operation ---
        o2_produced = 0
        for oxy in self.oxygenators:
            machine_power = self.cfg.oxygenator_power_cost # kWh cost to run machine
            needs_o2 = self.o2 < self.cfg.max_o2_tank
            if available_power >= machine_power and needs_o2:
                o2_produced += oxy.daily_check()
                available_power -= machine_power
                total_power_need += machine_power
            else:
                # Not enough power to run machine
                pass 

        water_reclaimed = 0
        for water_rec in self.water_reclaimers:
            machine_power = self.cfg.water_reclaimer_power_cost # kWh cost to run machine
            needs_water = self.water < self.cfg.max_water_tank
            if available_power >= machine_power and needs_water:
                # Logic: Can only process what is in the waste tank
                actual_processed = min(water_rec.daily_check(), self.waste_water)
                water_reclaimed += actual_processed
                self.waste_water -= actual_processed # Remove from waste tank
                available_power -= machine_power
                total_power_need += machine_power
            else:
                # Not enough power to run machine
                pass

        # --- 6. Update Resources ---
        
        # Power Balance
        self.battery += (power_gen - total_power_need)
        if self.battery > self.cfg.max_battery:
            self.battery = self.cfg.max_battery
        
        # Oxygen Balance
        self.o2 += (o2_produced + crop_o2_produced - total_o2_need)
        if self.o2 > self.cfg.max_o2_tank:
            self.o2 = self.cfg.max_o2_tank

        # Water Balance
        self.water += (water_reclaimed - total_water_need)
        if self.water > self.cfg.max_water_tank:
            self.water = self.cfg.max_water_tank

        # Food Balance
        self.food += (food_produced - total_food_need)
        
        # --- 7. Check Survival Conditions ---
        if self.battery < 0:
            self.alive = False
            self.cause_of_death = "Power Failure"
        
        elif self.o2 < 0:
            self.alive = False
            self.cause_of_death = "Suffocation"

        elif self.water < 0:
            self.alive = False
            self.cause_of_death = "Dehydration"

        elif self.food < 0:
            self.alive = False
            self.cause_of_death = "Starvation"

    def run_mission(self):
        """Runs the full MISSION_DURATION days or until death"""
        history = []
        for _ in range(MISSION_DURATION):
            if not self.alive:
                break
            self.step()
            history.append({
                'day': self.day,
                'o2': self.o2,
                'water': self.water,
                'waste_water': self.waste_water,
                'food': self.food,
                'crop_health': self.crops.health,
                'battery': self.battery,
                'storm': self.env.is_storming
            })
        return self.alive, self.cause_of_death, history
