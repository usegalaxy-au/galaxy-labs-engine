"""Custom exceptions."""

import logging
from pprint import pformat
from labs.lab_schema import (
    TabItem,
    TabSubsection,
    SectionTab,
)

logger = logging.getLogger('django')

LAB_SCHEMA_MODELS = {
    'TabItem': TabItem,
    'TabSubsection': TabSubsection,
    'SectionTab': SectionTab,
}


def _get_schema_help(loc):
    """Resolve schema model from error location and render help data."""
    for item in loc[::]:
        matched_keys = [k for k in LAB_SCHEMA_MODELS if k in str(item)]
        if matched_keys:
            return {
                'model_name': matched_keys[0],
                'schema': LAB_SCHEMA_MODELS[
                    matched_keys[0]
                ].model_json_schema()['properties'],
                'required_fields': LAB_SCHEMA_MODELS[
                    matched_keys[0]
                ].model_json_schema()['required'],
            }


class SubsiteBuildError(Exception):
    """Raised when an error occurs during subsite build."""

    def __init__(self, exc=None, url=None, section_id=None, source=''):
        """Initialize the exception."""
        self.title = (
            f"Error parsing {source} content from file"
            if source else None
        )
        self.url = url
        self.message = str(exc)
        self.section_id = section_id

        msg = (
            'Error processing exported lab content\n'
            f'URL: {url}\n'
            f'Errors:\n'
        )

        if hasattr(exc, 'errors'):
            # It's a Pydantic error. Extract info for rendering individual
            # messages
            self.errors = []
            for error in exc.errors():
                err = {
                    'message': error['msg'],
                    'location': f"section[{self.section_id}] > " + (
                        f'{error["loc"][0]} > '
                        + ' > '.join(str(x) for x in error["loc"][1:])
                    ),
                    'input': pformat(error['input']),
                    'help': _get_schema_help(error['loc']),
                }
                self.errors.append(err)
            msg += pformat(self.errors)
        else:
            msg += str(exc)

        logger.warning(exc)
        super().__init__(msg)
