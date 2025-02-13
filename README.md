# Galaxy Labs Engine

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

https://labs.usegalaxy.org.au/?content_root=https://raw.githubusercontent.com/my-username/my-labs-repo/my-lab/base.yml

To get a webpage like
[this](https://labs.usegalaxy.org.au/?content_root=https://github.com/usegalaxy-au/galaxy-labs-engine/blob/dev/app/labs/static/labs/content/simple/base.yml).

## How to Add Images to the Lab sections

1. Add the image URL to the `base.yml` file, e.g.,  
   ```yaml
   image_url: https://imageurl.com
   ```
2. Add the following `<div>` in the desired `section.yml` file:  

   ```html
   <div>
       <img src="{{ image_url }}" alt="Image title" style="max-width: 100%;">
       <p style="font-size: 0.9em;">
           Add image caption here
       </p>
   </div>
   ```

Please refer to the example in [this file](https://github.com/galaxyproject/galaxy_codex/blob/main/communities/microgalaxy/lab/sections/3_microbiome.yml).  
