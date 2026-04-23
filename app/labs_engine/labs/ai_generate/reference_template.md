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
item). The AI will translate each into a `sections/section_N.yml` file. There can be any number of sections and you choose what they're titled!

1. Getting started
2. Analysis tools
3. Learning resources


### Section 1: Getting started

Describe the purpose of this section in one or two sentences.

#### Tab 1: Data import (again, change tab names to anything you want)

Common tools for getting data into Galaxy (these should be full tool IDs - you can copy these from the menu bar at the top-right of any tool page on Galaxy: `Options > Copy tool ID`).
Each list item will become an expandable item, and tool metadata will be fetched if a tool ID is provided.

- upload1
- toolshed.g2.bx.psu.edu/repos/iuc/sra_tools/fasterq_dump

#### Tab 2: Example data

List any example datasets or histories you want to link to. Include
URLs where appropriate.

- https://mydata.com/dataset.txt

### Section 2: Analysis tools

What analyses does this Lab support? Provide a brief description here.

#### Tab 1: Quality control

A list of tools to help you with quality control.

- toolshed.g2.bx.psu.edu/repos/iuc/fastp/fastp

#### Tab 2: Assembly

- toolshed.g2.bx.psu.edu/repos/iuc/unicycler/unicycler


### Section 3: Learning resources

List any tutorials / learning pathways users should follow.

- https://training.galaxyproject.org/training-material/learning-pathways/intro-to-galaxy-and-genomics.html


## Conclusion

Anything else yto mention at the page e.g. connecting with community, feedback, contributions You can mention:

- A "Cite us" section with a DOI or preprint link.


## Help links

- [Galaxy support](https://galaxyproject.org/support/)
- [Galaxy help forum](https://help.galaxyproject.org)


## Footer
Any specific text you want shown in the page footer.
