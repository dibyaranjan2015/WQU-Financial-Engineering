import numpy as np

class FinancialPlanner:
    def __init__(self, return_rate: float):
        self.return_rate = return_rate # Annual return rate on investments
    
    def _get_accumulation_factor(self, years: int) -> float:
        return (1 + self.return_rate) * (((1 + self.return_rate) ** years - 1) / self.return_rate)
    
    def calculate_lump_sum_target(self, target_today: float, inflation_rate: float, accumulation_years: int) -> dict:
        fv_needed = target_today * ((1 + inflation_rate) ** accumulation_years)
        annuity_factor = self._get_accumulation_factor(accumulation_years)
        annual_contribution = fv_needed / annuity_factor
        
        return {
            "target_today": target_today, #Today's purchasing power requirement
            "fv_needed": fv_needed, # Future Value needed at retirement to maintain today's purchasing power
            "annual_contribution": annual_contribution, # Amount to save each year till retirement to meet the target
            "accumulation_years": accumulation_years, # Number of years to save before retirement
            "inflation_rate": inflation_rate # Annual inflation rate to adjust the target value for future purchasing power
        }
    
    def calculate_income_drawdown(self, annual_drawdown: float, drawdown_years: int, accumulation_years: int) -> dict:
        pv_at_retirement = annual_drawdown * (1 - (1 + self.return_rate) ** -drawdown_years) / self.return_rate
        annuity_factor = self._get_accumulation_factor(accumulation_years)
        annual_contribution = pv_at_retirement / annuity_factor
        
        return {
            "annual_drawdown": annual_drawdown,   #Desired annual income after retirement
            "nest_egg_needed": pv_at_retirement,  # Amount needed at retirement to fund the drawdown
            "annual_contribution": annual_contribution, # Amount to save each year till retirement
            "accumulation_years": accumulation_years,  # Number of years to save before retirement
            "drawdown_years": drawdown_years # Number of years to draw down the retirement income
        }
    
class TerminalInterface:

    @staticmethod
    def get_float_input(prompt: str, min_val: float = 0.0, max_val: float = None) -> float:
        while True:
            try:
                val = float(input(prompt).strip())
                if val < min_val:
                    print(f"⚠️ Input must be at least {min_val}. Please re-enter.")
                    continue
                if max_val is not None and val > max_val:
                    print(f"⚠️ Input cannot exceed {max_val}. Please re-enter.")
                    continue
                return val
            except ValueError:
                print("❌ Invalid entry. Please enter a valid decimal number.")
    
    @staticmethod
    def get_int_input(prompt: str, min_val: int = 1) -> int:
        """Guarantees a clean, validated time frame/integer value from user terminal input."""
        while True:
            try:
                val = int(input(prompt).strip())
                if val < min_val:
                    print(f"⚠️ Input must be at least {min_val}. Please re-enter.")
                    continue
                return val
            except ValueError:
                print("❌ Invalid entry. Please enter a whole integer.")

    def run(self):
        print("=" * 65)
        print("          RETIREMENT PLANNER       ")
        print("=" * 65)
        
        r_rate_pct = self.get_float_input("Enter expected portfolio investment Annual return rate (%) [e.g., 5]: ", min_val=0.0, max_val=100.0)
        planner = FinancialPlanner(return_rate = r_rate_pct / 100.0)
        
        print("\nSelect your primary wealth target methodology:")
        print("  [1] Target a specific Net Worth Goal (Adjusted dynamically for inflation)")
        print("  [2] Target a fixed Annual Retirement Income Stream ")
        
        choice = input("\nSelect strategy profile (1 or 2): ").strip()

        if choice == '1':
            print("\n--- Strategy: Purchasing Power Target ---")
            target_value = self.get_float_input("Target wealth goal in today's currency value: $")
            inflation_pct = self.get_float_input("Assumed annual inflation/discount rate (%) [e.g., 3]: ", min_val=0.0, max_val=50.0)
            horizon_years = self.get_int_input("Number of years remaining until retirement: ")
            
            res = planner.calculate_lump_sum_target(target_value, inflation_pct / 100.0, horizon_years)
            
            print("\n" + "-" * 45)
            print("                 VALUATION SUMMARY               ")
            print("-" * 45)
            print(f"Target Value (Today's Capital):  ${res['target_today']:,.2f}")
            print(f"Adjusted Target (Nominal FV):    ${res['fv_needed']:,.2f}")
            print(f"Accumulation Horizon:            {res['accumulation_years']} Years")
            print(f"Assumed Investment Return:       {r_rate_pct/100:.2%}")
            print(f"Assumed Core Inflation:          {inflation_pct / 100.0:.2%}")
            print("-" * 45)
            print(f"🚀 REQUIRED ANNUAL DEPOSIT:      ${res['annual_contribution']:,.2f}")
            print("-" * 45)

        elif choice == '2':
            print("\n--- Strategy: Retirement Income Stream ---")
            drawdown_income = self.get_float_input("Desired annual retirement payout: $")
            drawdown_duration = self.get_int_input("Number of years retirement payouts must last: ")
            horizon_years = self.get_int_input("Number of years remaining until retirement begins: ")
            
            res = planner.calculate_income_drawdown(drawdown_income, drawdown_duration, horizon_years)
            
            print("\n" + "-" * 45)
            print("                 VALUATION SUMMARY               ")
            print("-" * 45)
            print(f"Target Retirement Income Stream: ${res['annual_drawdown']:,.2f} / Year")
            print(f"Amount needed at retirement to fund the drawdown:  ${res['nest_egg_needed']:,.2f}")
            print(f"Annuity Drawdown Window:         {res['drawdown_years']} Years")
            print(f"Accumulation Horizon:            {res['accumulation_years']} Years")
            print(f"Assumed Investment Return:       {r_rate_pct/100:.2%}")
            print("-" * 45)
            print(f"🚀 REQUIRED ANNUAL DEPOSIT:      ${res['annual_contribution']:,.2f}")
            print("-" * 45)
            
        else:
            print("\n❌ Action aborted: Invalid profile selection choice.")
        
        print("=" * 65)

if __name__ == "__main__":
    app = TerminalInterface()
    app.run()