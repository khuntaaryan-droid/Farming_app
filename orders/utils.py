from decimal import Decimal

def calculate_delivery_cost(buyer, farmers_in_cart):
    """
    Calculates estimated delivery cost based on city/state matching.
    Low (₹50): Same city and state.
    Medium (₹150): Same state, different city.
    High (₹300): Different state.
    
    If multiple farmers are involved, we take the highest cost among them, 
    or we could sum them. Let's sum them for a realistic marketplace model.
    """
    total_cost = Decimal('0.00')
    
    if not buyer.is_authenticated:
        # Default fallback for anonymous (shouldn't happen in this app's flow)
        return Decimal('150.00') * len(farmers_in_cart)
        
    buyer_city = buyer.village_or_city.lower().strip()
    buyer_state = buyer.state.lower().strip()
    
    for farmer in farmers_in_cart:
        farmer_city = farmer.village_or_city.lower().strip()
        farmer_state = farmer.state.lower().strip()
        
        if buyer_state == farmer_state:
            if buyer_city == farmer_city:
                total_cost += Decimal('50.00')  # Low
            else:
                total_cost += Decimal('150.00') # Medium
        else:
            total_cost += Decimal('300.00')     # High
            
    return total_cost
