import datetime

class CreditRiskEngine:
    def __init__(self, base_rate: float):
        self.base_rate = base_rate  # Base interest rate for credit risk calculations
    
    def evaluate_counterparty(self, principal: float, credit_score: int, has_bankruptcy: bool) -> dict:

        risk_premium = 0;
        if credit_score <600:
            risk_premium += 0.05  # High risk premium for low credit score
        elif credit_score <700:
            risk_premium += 0.02  # Moderate risk premium for average credit score

        if has_bankruptcy:
            risk_premium += 0.10  # Additional risk premium for bankruptcy history

        final_rate = self.base_rate + risk_premium
        total_due = principal * (1 + final_rate)

        if credit_score < 600 or has_bankruptcy:
            pd = 0.25 # High probability of default
        elif credit_score < 700:
            pd = 0.08 # Moderate probability of default
        else:
            pd = 0.02 # Low probability of default
        
        expected_loss = total_due * pd
        expected_recovery = total_due - expected_loss

        return {
            "final_rate": final_rate,  # Final interest rate after risk adjustments
            "total_due": total_due,    # Total amount due including principal and interest  
            "probability_of_default": pd,  # Probability of default based on credit score and history
            "expected_loss": expected_loss,  # Expected loss due to default 
            "expected_recovery": expected_recovery  # Expected amount recoverable after default
        }


class CollateralManager:
    @staticmethod

    def calculate_loss_given_default(outstanding_balance: float, collateral_market_value: float, haircut: float) -> dict:
        
        liquidation_value = collateral_market_value * (1 - haircut) # haircut is the percentage reduction in collateral value to account for market volatility and liquidation costs
        recovered_amount = min(liquidation_value, outstanding_balance)
        net_credit_loss = outstanding_balance - recovered_amount

        return {
            "liquidation_value": liquidation_value,  # Value of collateral after applying haircut
            "recovered_amount": recovered_amount,    # Amount recovered from collateral liquidation
            "net_credit_loss": net_credit_loss       # Net loss after accounting for recovered collateral
            }


class CreditRiskInterface:

    @staticmethod
    def _get_float_input(prompt:str) -> float:
        while True:
            try:
                val = float(input(prompt).strip())
                if val < 0:
                    print("⚠️ Input must be a non-negative number. Please re-enter.")
                    continue
                return val
            except ValueError:
                print("❌ Invalid entry. Please enter a valid decimal number.")
    
    @staticmethod
    def _get_int_input(prompt:str) -> int:
        while True:
            try:
                val = int(input(prompt).strip())
                if val < 0:
                    print("⚠️ Input must be a non-negative integer. Please re-enter.")
                    continue
                return val
            except ValueError:
                print("❌ Invalid entry. Please enter a whole integer.")

    def run(self):
        print("=" * 65)
        print("            CREDIT RISK ENGINE INTERFACE      ")
        print("=" * 65)
        print("1. Counterparty Credit Risk Pricing Engine")
        print("2. Collateral Liquidation & LGD Simulator")
        
        choice = input("\nSelect core asset engine (1-2): ").strip()

        if choice == '1':
            print("\n--- Counterparty Credit Risk Pricing Engine ---")
            base_rate = self._get_float_input("Enter base interest rate (as decimal, e.g., 0.05 for 5%): ")
            principal = self._get_float_input("Enter principal amount: ")
            credit_score = self._get_int_input("Enter counterparty credit score (300-850): ")
            has_bankruptcy = input("Has the counterparty declared bankruptcy before? (y/n): ").strip().lower() == 'y'

            engine = CreditRiskEngine(base_rate)
            result = engine.evaluate_counterparty(principal, credit_score, has_bankruptcy)

            print("\n--- Credit Risk Evaluation Result ---")
            print(f"Final Interest Rate: {result['final_rate']:.2%}")
            print(f"Total Amount Due: ${result['total_due']:,.2f}")
            print(f"Probability of Default: {result['probability_of_default']:.2%}")
            print(f"Expected Loss: ${result['expected_loss']:,.2f}")
            print(f"Expected Recovery: ${result['expected_recovery']:,.2f}")

        elif choice == '2':
            print("\n--- Collateral Liquidation & LGD Simulator ---")
            outstanding_balance = self._get_float_input("Enter outstanding balance: ")
            collateral_market_value = self._get_float_input("Enter collateral market value: ")
            haircut = self._get_float_input("Enter haircut percentage (Discount in liquidating the collateral) (as decimal, e.g., 0.2 for 20%): ")

            result = CollateralManager.calculate_loss_given_default(outstanding_balance, collateral_market_value, haircut)

            print("\n--- Collateral Liquidation Result ---")
            print(f"Liquidation Value of Collateral: ${result['liquidation_value']:,.2f}")
            print(f"Recovered Amount from Collateral: ${result['recovered_amount']:,.2f}")
            print(f"Net Credit Loss: ${result['net_credit_loss']:,.2f}")
        
        else:
            print("❌ Invalid selection. Please restart and choose a valid option (1 or 2).")


if __name__ == "__main__":
    interface = CreditRiskInterface()
    interface.run()

