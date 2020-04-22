from django.db import models

class Feedback(models.Model):
    ratingTypes=(
        ("Poor","Poor"),
        ("Average","Average"),
        ("Satisfactory","Satisfactory"),
        ("Good","Good"),
        ("Excellent","Excellent"),
    )
    name = models.CharField(max_length=30)
    email = models.EmailField()
    rating  =models.CharField(max_length=20,choices=ratingTypes)
    text = models.CharField(max_length=100)
# Create your models here.
