from django.forms import ModelForm

from .models import BpmPlaylist

class BpmPlaylistForm(ModelForm):
    class Meta:
        model = BpmPlaylist
        fields = ['name','bpm_start','bpm_end','multiples_bpm']
