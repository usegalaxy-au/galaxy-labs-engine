# Galaxy Labs Engine


## Building a lab page with GitPod

Open a terminal (CTRL+`) and you'll see the external URL for your test lab:

```sh
echo http://127.0.0.1:8000/lab/export?content_root=${GITPOD_WORKSPACE_URL}/static/dev-lab/base.yml
```

Now add/edit your content in the `test-lab` folder, refresh the page and see your content appear on the web page!


## About the Labs Engine

This site presents a public rending engine for creating Galaxy Lab landing
pages (known as the 'Welcome page' in Galaxy terms) from content hosted on
GitHub.

Create a lab content directory like
[this](./app/labs/content/simple/):

```
.
├── base.yml
├── section_1.yml
├── section_2.yml
├── static
│   ├── custom.css
│   └── logo.svg
└── templates
    ├── conclusion.md
    ├── footer.md
    └── intro.md
```

And then request your page anywhere like this:

`https://${LABS_HOSTNAME}/export/?content_root=https://raw.githubusercontent.com/my-username/my-labs-repo/my-lab/base.yml`

To get a webpage like
[this](https://{LABS_HOSTNAME}/export/?content_root=https://raw.githubusercontent.com/neoformit/galaxy-labs-engine/dev/app/labs/content/simple/main.yml).
