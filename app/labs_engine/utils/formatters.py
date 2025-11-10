"""For formatting data."""

from urllib.parse import urlparse, parse_qs


class EmbeddedYouTubeUrl:
    """Class to format youtube video URLs.

    https://youtu.be/O0FQa1SViZA?si=Ejk2AqUTIPk2FSMC
    """

    def __init__(self, raw_url):
        """Initialize video URL formatter."""
        self.raw_url = raw_url
        self.formatted_url = self._format()

    def __str__(self):
        """Return formatted URL as string."""
        return self.formatted_url or ''

    def __bool__(self):
        """Return True if formatted URL exists."""
        return bool(self.formatted_url)

    def _format(self):
        """Reformat YouTube video URLs to embed format."""
        url = self.raw_url
        if (
            url
            and (
                'youtube.com' in url
                or 'youtu.be' in url
            )
        ):
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            if 'v' in params:
                video_id = params['v'][0]
                join_char = '&' if '?' in video_id else '?'
                url = (
                    'https://www.youtube.com/embed/'
                    f'{video_id}{join_char}rel=0&showinfo=0'
                )
            elif 'youtu.be/' in url:
                video_id = url.split('/')[-1]
                join_char = '&' if '?' in video_id else '?'
                url = (
                    'https://www.youtube.com/embed/'
                    f'{video_id}{join_char}rel=0&showinfo=0'
                )
        return url
