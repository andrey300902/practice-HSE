from django import forms

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import datetime #for checking renewal date range.

class MatrixForm(forms.Form):
    vector = forms.CharField()
    mode = forms.BooleanField(required=False)
    type = forms.BooleanField(required=False)

class NameForm(forms.Form):
    move = forms.CharField()

