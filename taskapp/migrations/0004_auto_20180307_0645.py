# Generated by Django 2.0.3 on 2018-03-07 06:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taskapp', '0003_auto_20180307_0618'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=1000)),
                ('created', models.DateTimeField(auto_now=True)),
                ('score', models.IntegerField()),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taskapp.Company')),
            ],
        ),
        migrations.CreateModel(
            name='UserScoreHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('created', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='usersetup',
            name='score',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='companytask',
            name='deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userscorehistory',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taskapp.UserSetup'),
        ),
    ]
