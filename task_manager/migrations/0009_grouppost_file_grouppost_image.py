# Generated by Django 5.2.1 on 2025-05-16 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_manager', '0008_group_grouppost_groupcomment_grouptask_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='grouppost',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='group_posts/files/', verbose_name='Döküman'),
        ),
        migrations.AddField(
            model_name='grouppost',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='group_posts/images/', verbose_name='Görsel'),
        ),
    ]
