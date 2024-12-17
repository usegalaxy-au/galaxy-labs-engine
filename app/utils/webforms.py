"""Utilities for Django forms."""

import logging
from django import forms
from django.utils.safestring import mark_safe

logger = logging.getLogger('django')


class SubmitDelaySpamFilterMixin(forms.Form):
    """Enforce a submit delay to prevent spam/bot submissions."""

    SUBMIT_DELAY_MINIMUM_SECONDS = 3.0

    submit_delay_seconds = forms.FloatField(
        min_value=SUBMIT_DELAY_MINIMUM_SECONDS, required=False)

    submit_delay_field_html = """
        <script>
        const initTime = new Date();
        const setSubmitDelay = () => {
            const submitDelaySeconds = (new Date() - initTime) / 1000;
            const submitDelayInput = $(
                `<input
                type="hidden"
                name="submit_delay_seconds"
                value="${submitDelaySeconds}"
                >`);
            $('form').append(submitDelayInput);
        }
        $('form').submit(setSubmitDelay);
        </script>
    """


class HoneypotSpamFilterMixin(forms.Form):
    """Include a honeypot field to catch spam/bot submissions."""

    DELAY_DISABLE_MS = 1000
    HONEYPOT_FIELD_NAME = 'institution_hp'
    institution_hp = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    honeypot_field_html = f"""
        <input
            type="text"
            name="{HONEYPOT_FIELD_NAME}"
            id="id_{HONEYPOT_FIELD_NAME}"
            required
        />
        <script type="text/javascript">
            setTimeout( () => $("#id_{HONEYPOT_FIELD_NAME}")
                .prop("disabled", 1), {DELAY_DISABLE_MS});
            $("#id_{HONEYPOT_FIELD_NAME}").css("position", "absolute");
            $("#id_{HONEYPOT_FIELD_NAME}").css("bottom", "0");
            $("#id_{HONEYPOT_FIELD_NAME}").css("right", "0");
            $("#id_{HONEYPOT_FIELD_NAME}").css("opacity", "0");
        </script>"""

    def clean_institution_hp(self):
        """Check honeypot field."""
        value = self.cleaned_data.get(self.HONEYPOT_FIELD_NAME)
        if value:
            logger.warning('Honeypot field was filled in.')
            raise forms.ValidationError('This value is incorrect.')
        return value


class SpamFilterFormMixin(
    SubmitDelaySpamFilterMixin,
    HoneypotSpamFilterMixin,
):
    """A base form with multiple levels of spam filtering/prevention."""

    INTERNAL_FIELDS = (
        'submit_delay_seconds',
        'institution_hp',
        'captcha',
    )
    antispam_html = mark_safe(
        HoneypotSpamFilterMixin.honeypot_field_html
        + SubmitDelaySpamFilterMixin.submit_delay_field_html)
