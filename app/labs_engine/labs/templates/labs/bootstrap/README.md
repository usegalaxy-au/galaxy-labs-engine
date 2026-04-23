# What to do next?

1. If you want to view your changes instantly, you can try [rendering your Lab Page locally](https://labs.usegalaxy.org.au/#section_1-faq-2-accordion).
2. To publish, copy the downloaded Lab content folder to a public-facing Github repository.
3. On GitHub, navigate to the `base.yml` file of your Lab content folder and
   copy the URL - we will refer to this as `MY_GITHUB_URL`. e.g.
   `https://github.com/mygithubuser/my-repo-name/blob/main/base.yml`
4. View your Lab page in real time by visiting:
   `https://labs.usegalaxy.org.au/?content_root=MY_GITHUB_URL/base.yml``
5. Update the content of the Lab by editing the files in your repository on Github.
6. To view updated content, you should disable caching with an additional URL parameter:
   `https://labs.usegalaxy.org.au/?content_root=MY_GITHUB_URL/base.yml&cache=false`
7. You can switch between different Galaxy server's versions of the page by
   pointing to the server's YAML file e.g. replace `base.yml` with
   `usegalaxy.eu.yml` in `MY_GITHUB_URL`.
8. When writing HTML/Markdown Lab content, try to use the variables defined in
   `base.yml` as much as possible, for example `Welcome to Galaxy Europe!`,
   should be written like `Welcome to Galaxy {% verbatim %}{{ site_name }}{% endverbatim %}!`
9. Any variables that you add to `base.yml` or `<server>.yml` can be referenced in
   Markdown/HTML!

For full docs on building a Lab page, go to [https://labs.usegalaxy.org.au/](https://labs.usegalaxy.org.au/).
