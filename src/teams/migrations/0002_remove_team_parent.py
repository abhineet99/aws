# Generated by Django 3.0.4 on 2020-04-05 12:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='parent',
        ),
    ]