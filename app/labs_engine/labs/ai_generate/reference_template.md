# My Galaxy Lab

This is a template for describing a Galaxy Lab in Markdown. The "Bootstrap a
Lab" feature on the Galaxy Labs Engine will pass this file to an AI model to
generate a fully-structured Lab content folder (templates, sections, base.yml,
server YAMLs).

Only the headings matter; feel free to rearrange or expand the body text.
Delete any sections or tabs you don't need.


## Intro

Write a friendly, 1-3 paragraph welcome message for users of your Lab.

You can mention things you want embedded, e.g.:
- An embedded video:
  [Title of video](https://youtu.be/XXXXXXXXXXX)
- An image at `static/some-image.png` (you will need to add the image to the
  generated archive yourself).


## Sections

Briefly list the sections that should appear on the page (one per numbered
item). The AI will translate each into a `sections/section_N.yml` file.

1. Getting started
2. Analysis tools
3. Learning resources


### Section 1: Getting started

Describe the purpose of this section in one or two sentences.

#### Tab 1: Data import

Common tools for getting data into Galaxy.

- upload1
- toolshed.g2.bx.psu.edu/repos/iuc/sra_tools/fasterq_dump

#### Tab 2: Example data

Describe any example datasets or histories you want to link to. Include
URLs where appropriate.


### Section 2: Analysis tools

What analyses does this Lab support? Briefly describe.

#### Tab 1: Quality control

- toolshed.g2.bx.psu.edu/repos/iuc/fastp/fastp

#### Tab 2: Assembly

- toolshed.g2.bx.psu.edu/repos/iuc/unicycler/unicycler


### Section 3: Learning resources

List any tutorials / learning pathways users should follow.

- https://training.galaxyproject.org/training-material/learning-pathways/intro-to-galaxy-and-genomics.html


## Conclusion

One or two paragraphs wrapping up the page. You can mention:

- A feedback form (the Lab Engine provides one out of the box).
- A "Cite us" section with a DOI or preprint link.
- An embedded site footer.


## Help links

- [Galaxy support](https://galaxyproject.org/support/)
- [Galaxy help forum](https://help.galaxyproject.org)
