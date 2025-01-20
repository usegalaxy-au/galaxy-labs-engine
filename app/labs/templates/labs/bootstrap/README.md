# What to do next?

1. Copy this Lab content folder to a public-facing Github repository.
2. On GitHub, navigate to the `base.yml` file of your Lab content folder and
   copy the URL - we will refer to this as `MY_GITHUB_URL`. e.g.
   https://github.com/mygithubuser/my-repo-name/blob/main/base.yml
3. View your Lab page in real time by visiting:
   https://labs.usegalaxy.org.au/?content_root=`MY_GITHUB_URL/base.yml`
4. Update the content of the Lab by editing the files in your repository on Github.
5. To view updated content, you must disable caching with an extra URL parameter:
   https://labs.usegalaxy.org.au/?content_root=`MY_GITHUB_URL/base.yml&cache=false`
6. You can switch between different Galaxy server's versions of the page by
   pointing to the server's YAML file e.g. replace `base.yml` with
   `usegalaxy.eu.yml` in MY_GITHUB_URL.
7. When writing HTML/Markdown Lab content, try to use the variables defined in
   `base.yml` as much as possible, for example `Welcome to Galaxy Europe!`,
   should be written like `Welcome to Galaxy {{ site_name }}!`
8. Any variables that you add to `base.yml` or `<server>.yml` can be referenced in
   Markdown/HTML!

For full docs on building a Lab page, go to https://labs.usegalaxy.org.au/.
