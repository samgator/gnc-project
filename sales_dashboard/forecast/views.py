from django.shortcuts import render
from .models import SalesForecast

def forecast_chart(request):
    data = SalesForecast.objects.order_by('date')
    labels = [entry.date.strftime('%Y-%m-%d') for entry in data]
    values = [entry.predicted_sales for entry in data]

    return render(request, 'forecast/chart.html', {
        'labels': labels,
        'values': values,
    })