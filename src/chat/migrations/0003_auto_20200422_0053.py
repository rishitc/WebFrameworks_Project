# Generated by Django 3.0.5 on 2020-04-21 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='profile_image_height',
            field=models.BigIntegerField(blank=True, default=200, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='profile_image_width',
            field=models.BigIntegerField(blank=True, default=200, null=True),
        ),
    ]
