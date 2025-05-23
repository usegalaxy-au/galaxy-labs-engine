"""User facing forms for making support requests (help/tools/data)."""

import logging
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Submit
from django import forms
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.validators import FileExtensionValidator
from utils.mail import retry_send_mail
from utils.webforms import SpamFilterFormMixin

from . import bootstrap, validators

logger = logging.getLogger('django')

MAIL_APPEND_TEXT = f"Sent from {settings.HOSTNAME}"
IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
INTRO_MD = 'Welcome to the Galaxy {{ site_name }} {{ lab_name }}!'
CONCLUSION_MD = ('Thanks for checking out the Galaxy {{ site_name }}'
                 ' {{ lab_name }}!')
FOOTER_MD = f"""
<footer class="text-center">
    This page was generated by the
    <a href="https://{settings.HOSTNAME}/bootstrap">Galaxy Labs Engine</a>.
</footer>
"""


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


class LabBootstrapForm(SpamFilterFormMixin, forms.Form):
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
        help_text=(
            "The subdomain that the lab will be served under. i.e."
            " &lt;subdomain&gt;.usegalaxy.org"
        ),
    )
    github_username = forms.CharField(
        label="GitHub Username",
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
        }),
        help_text=(
            '(Optional) Your GitHub username to add to the list of'
            ' contributors.'
        ),
        validators=[validators.validate_github_username],
        required=False,
    )
    logo = forms.FileField(
        label="Lab logo",
        help_text=("(Optional) Upload a custom logo to be displayed in the Lab"
                   " header. Try to make it square and less than 100KB"
                   " - SVG format is highly recommended."),
        required=False,
        allow_empty_file=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=IMAGE_EXTENSIONS,
            ),
        ],
        widget=forms.FileInput(attrs={
            'accept': ','.join(f"image/{ext}" for ext in IMAGE_EXTENSIONS),
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'lab_name',
            'subdomain',
            'github_username',
            'logo',
            HTML(self.antispam_html),
            Submit('submit', 'Build'),
        )

    def clean_subdomain(self):
        """Validate the subdomain."""
        subdomain = self.cleaned_data['subdomain'].lower().strip()
        if not subdomain.isalnum():
            raise forms.ValidationError("Subdomain must be alphanumeric.")
        return subdomain

    def clean_lab_name(self):
        """Validate the lab name."""
        lab_name = self.cleaned_data['lab_name'].title().strip()
        if not lab_name.replace(' ', '').isalnum():
            raise forms.ValidationError("Lab name cannot be empty.")
        return lab_name

    def clean_github_username(self):
        username = self.cleaned_data.get('github_username')
        return username.strip() if username else None

    def bootstrap_lab(self):
        data = self.cleaned_data
        data.update({
            'intro_md': INTRO_MD,  # TODO: Render from user-input
            'conclusion_md': CONCLUSION_MD,
            'footer_md': FOOTER_MD,
            'root_domain': 'usegalaxy.org',
            'galaxy_base_url': (
                f"https://{data['subdomain']}.usegalaxy.org"),
            'section_paths': [
                'sections/section-1.yml',  # TODO: Auto-render from user input
            ],
        })
        return bootstrap.lab(data)
