# Generated by Django 2.2 on 2020-07-03 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0004_item_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
