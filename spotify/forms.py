from django.forms import ModelForm

from .models import BpmPlaylist

class BpmPlaylistForm(ModelForm):
    class Meta:
        model = BpmPlaylist
        fields = ['name','bpm_start','bpm_end','multiples_bpm']
        error_messages = {
            'name': {
                'max_length': "The name is too long. It must be less than or equal to 50 characters.",
            },
        }
