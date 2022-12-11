from math import ceil
from django.shortcuts import render
from .models import Product
from mainapp import keys

# Create your views here.
def home(request):
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil(n/4) - (n // 4)
        allProds.append([prod, range(1, nSlides), nSlides])

    params = {'allProds': allProds}
    return render(request, 'index.html', params)

def purchase(request):
    return render(request, "purchase.html", params)