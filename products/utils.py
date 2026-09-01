from .models import Product, PriceReference

def get_crop_recommendations():
    """
    Analyzes supply and demand for crops.
    Returns a list of dictionaries with crop name, supply status, and recommendation.
    """
    # Get all unique crop names from PriceReference as our base "known" crops
    known_crops = PriceReference.objects.values_list('crop_name', flat=True).distinct()
    
    recommendations = []
    
    for crop in known_crops:
        # Calculate supply (number of active listings for this crop)
        # Using icontains because our Product names might be "Fresh Tomato" or "Red Tomato"
        supply_count = Product.objects.filter(is_active=True, name__icontains=crop).count()
        
        status = 'Balanced'
        message = 'Normal market conditions.'
        color = 'primary'
        
        if supply_count > 5:
            status = 'Oversupplied'
            message = 'High competition right now. Prices may drop.'
            color = 'danger'
        elif supply_count < 2:
            status = 'High Demand'
            message = 'Low supply in the market. Great time to list!'
            color = 'success'
            
        recommendations.append({
            'crop_name': crop,
            'supply_count': supply_count,
            'status': status,
            'message': message,
            'color': color
        })
        
    return recommendations
