# Generated by Django 4.0.4 on 2022-04-25 03:34

import annoying.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpotifyUser',
            fields=[
                ('user', annoying.fields.AutoOneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('spotify_user_id', models.CharField(max_length=50, unique=True)),
                ('spotify_display_name', models.CharField(max_length=191)),
                ('access_token', models.CharField(default='', max_length=50)),
                ('refresh_token', models.CharField(default='', max_length=50)),
                ('expiration', models.DateTimeField(default=None)),
                ('scope', models.CharField(default='', max_length=191)),
                ('date_auth', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='BpmPlaylist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playlist_id', models.CharField(default=None, max_length=200, unique=True)),
                ('created_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_update_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('public', models.BooleanField(default=True)),
                ('bpm_start', models.DecimalField(decimal_places=3, max_digits=7)),
                ('bpm_end', models.DecimalField(decimal_places=3, max_digits=7)),
                ('multiples_bpm', models.BooleanField(default=True)),
                ('spotify_user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='spotify.spotifyuser')),
            ],
        ),
    ]
