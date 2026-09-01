from django import forms
from .models import Product, CropDiseaseQuery, AgroProduct

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'image', 'price_per_unit', 'unit', 'quantity_available', 'bulk_price_threshold', 'bulk_price_per_unit', 'is_organic', 'harvest_date', 'is_active']
        widgets = {
            'harvest_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['is_organic', 'is_active']:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'

class CropDiseaseQueryForm(forms.ModelForm):
    class Meta:
        model = CropDiseaseQuery
        fields = ['crop_name', 'symptoms', 'image']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class AgroProductForm(forms.ModelForm):
    class Meta:
        model = AgroProduct
        fields = ['name', 'category', 'description', 'usage_guidance', 'price', 'image', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'
