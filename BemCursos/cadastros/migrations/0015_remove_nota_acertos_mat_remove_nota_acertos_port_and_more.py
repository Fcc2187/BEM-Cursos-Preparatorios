# Generated by Django 5.1 on 2024-10-26 14:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0014_nota'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nota',
            name='acertos_mat',
        ),
        migrations.RemoveField(
            model_name='nota',
            name='acertos_port',
        ),
        migrations.RemoveField(
            model_name='nota',
            name='usuario',
        ),
        migrations.AddField(
            model_name='nota',
            name='aluno',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='cadastros.aluno'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='nota',
            name='matematica_acertos',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='nota',
            name='portugues_acertos',
            field=models.IntegerField(default=0),
        ),
    ]