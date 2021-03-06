# Generated by Django 3.0.7 on 2020-06-16 13:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '__first__'),
        ('workflows', '__first__'),
        ('teams', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormBlueprint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=128)),
                ('active', models.BooleanField(default=True)),
                ('saved', models.BooleanField(default=False)),
                ('workflow', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='workflows.Workflow')),
            ],
        ),
        migrations.CreateModel(
            name='FormInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
                ('creation_time', models.DateTimeField(auto_now=True)),
                ('blueprint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='forms.FormBlueprint')),
                ('current_node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflows.Node')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.Profile')),
            ],
        ),
        migrations.CreateModel(
            name='FormNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('F', 'Forwarded'), ('B', 'Sent Back for comments'), ('N', 'No Action Taken')], default='N', max_length=2)),
                ('form_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forms.FormInstance')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.TeamHasEmployees')),
            ],
        ),
        migrations.CreateModel(
            name='FormInstanceHasComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField()),
                ('active', models.BooleanField(default=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('form_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forms.FormInstance')),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiver', to='employees.Profile')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sender', to='employees.Profile')),
            ],
        ),
    ]
