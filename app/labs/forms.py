"""User facing forms for making support requests (help/tools/data)."""

import logging
from django import forms
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from utils.mail import retry_send_mail

from . import bootstrap

logger = logging.getLogger('django')

MAIL_APPEND_TEXT = f"Sent from {settings.HOSTNAME}"


def dispatch_form_mail(
        to_address=None,
        reply_to=None,
        subject=None,
        text=None,
        html=None):
    """Send mail to support inbox.

    This should probably be sent to a worker thread but the SMTP server
    responds very quickly in production.
    """
    recipient = to_address or settings.EMAIL_TO_ADDRESS
    reply_to_value = [reply_to] if reply_to else None
    logger.info(f"Sending mail to {recipient}")
    text += f"\n\n\n{MAIL_APPEND_TEXT}"
    email = EmailMultiAlternatives(
        subject,
        text,
        settings.EMAIL_FROM_ADDRESS,
        [recipient],
        reply_to=reply_to_value,
    )
    if html:
        html = html.replace(
            '</body>',
            f'<small style="color: gray;">{MAIL_APPEND_TEXT}</small>\n</body>'
        )
        email.attach_alternative(html, "text/html")
    retry_send_mail(email)


class SupportRequestForm(forms.Form):
    """Form to request for user support."""

    name = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField()

    def dispatch(self, subject=None):
        """Dispatch content via the FreshDesk API."""
        data = self.cleaned_data
        dispatch_form_mail(
            reply_to=data['email'],
            subject=subject or "Galaxy Australia Support request",
            text=(
                f"Name: {data['name']}\n"
                f"Email: {data['email']}\n\n"
                + data['message']
            )
        )


class LabFeedbackForm(SupportRequestForm):

    to_address = forms.EmailField(required=False)

    def dispatch(self, subject=None):
        """Dispatch content via the FreshDesk API."""
        data = self.cleaned_data
        dispatch_form_mail(
            to_address=data['to_address'] or settings.EMAIL_TO_ADDRESS,
            reply_to=data['email'],
            subject=subject or "Galaxy Australia Lab feedback",
            text=(
                f"Name: {data['name']}\n"
                f"Email: {data['email']}\n\n"
                + data['message']
            )
        )


class LabBootstrapForm(forms.Form):
    """Form to bootstrap a new lab."""

    lab_name = forms.CharField(
        label="Lab name",
        widget=forms.TextInput(attrs={
            'placeholder': "e.g. Genome Lab",
            'autocomplete': 'off',
        }),
    )
    subdomain = forms.CharField(
        label="Galaxy Lab Subdomain",
        widget=forms.TextInput(attrs={
            'placeholder': "e.g. genome",
            'autocomplete': 'off',
        }),
        help_text="The subdomain that the lab will be served under.",
    )
    logo = forms.FileField(
        label="Lab logo",
        help_text=("(Optional) Upload a custom logo to be displayed in the Lab"
                   " header."),
        required=False,
    )
    # sections_json = forms.CharField()

    # def clean_section_json(self):
    #     """Validate the section JSON."""
    #     try:
    #         data = json.loads(self.cleaned_data['sections_json'])
    #         # Validate with Pydantic models...?
    #     except Exception as exc:
    #         raise forms.ValidationError(f"Invalid JSON: {exc}")

    #     return data

    def bootstrap_lab(self):
        return bootstrap.lab(self.cleaned_data)
