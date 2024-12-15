# What to do next?

1. Copy this Lab content folder to a public-facing Github repository.
1. On GitHub, navigate to the root of your Lab content folder and copy the URL -
   we will refer to this as `MY-GITHUB-URL`.
1. View your Lab page in real time by visiting:
   https://labs.usegalaxy.org.au/content_root=`MY-GITHUB-URL/base.yml`
1. Update the content of the Lab by editing the files in your repository on Github.
1. To view updated content, you must disable caching with an extra URL parameter:
   https://labs.usegalaxy.org.au/content_root=`MY-GITHUB-URL/base.yml&cache=false`
1. You can switch between different Galaxy server's versions of the page by
   pointing to the server's YAML file e.g. `MY-GITHUB-URL/usegalaxy.eu.yml`.
1. When writing HTML/Markdown Lab content, try to use the variables defined in
   `base.yml` as much as possible, for example `Welcome to Galaxy Europe!`,
   should be written like `Welcome to Galaxy {{ site_name }}!`
1. Any variables that you add to `base.yml` or `<server>.yml` can be referenced in
   Markdown/HTML!

For full docs on building a Lab page, go to https://labs.usegalaxy.org.au/.
