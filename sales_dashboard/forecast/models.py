from django.db import models

class SalesForecast(models.Model):
    date = models.DateField()
    predicted_sales = models.FloatField()

    def __str__(self):
        return f'{self.date}: {self.predicted_sales}'