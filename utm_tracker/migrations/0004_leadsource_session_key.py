# Generated by Django 3.1.5 on 2021-01-19 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utm_tracker', '0003_increase_medium_chars'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadsource',
            name='session_key',
            field=models.CharField(blank=True, default='', help_text='The session in which the params were captured.', max_length=40),
        ),
    ]
