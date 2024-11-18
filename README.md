<div align="center" markdown>

<img src="https://github.com/user-attachments/assets/99da5427-fe7c-4d5d-a33e-94592b8933b3"/>

# Review Image Annotations in Batches

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervisely.com/apps/supervisely-ecosystem/review-image-annotations-in-batches)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/review-image-annotations-in-batches)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/review-image-annotations-in-batches.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/review-image-annotations-in-batches.png)](https://supervisely.com)

</div>

## Overview

The **Review Image Annotations in Batches** application allows for batch review of image annotations.

Through its settings, you can:

- Select the batch size, which determines the grid size of images for visualization
- Set a default value that will predetermine the decision for each image in the batch before the actual review
- Precisely filter by tags and classes
- Group images by tag or class criteria
- Edit tags directly during the review process

## Preparation

Before you can try this application in action, you need to have a Labeling Job ready for review.
To learn more about what a Labeling Job is, how to create it, and what the review process involves, you can read [this article](https://supervisely.com/blog/labeling-jobs/) or watch video.

<a data-key="sly-embeded-video-link" href="https://youtu.be/YwNHbvyZL7Q" data-video-code="YwNHbvyZL7Q">  
    <img src="https://github.com/user-attachments/assets/e1c26f0f-1d4f-463a-8401-5460bbaad946">
</a>

## How To Run

1. Launch the application.
2. Select the Labeling Job you want to review.
3. Configure your Workbench in **Review Settings** for optimal convenience during the process.
   ![](https://github.com/user-attachments/assets/206cc671-ed07-4355-b674-043e26f6a48d)
4. Click the **Start Review** button to begin.

During the review, the application arranges a grid of images, displaying their annotations: tags and object classes.
![](https://github.com/user-attachments/assets/0aeaf069-e95a-437f-bcae-db4ec2298612)
Each image has its own decision selector.

![](https://github.com/user-attachments/assets/6bc77763-89f2-4b3f-be17-4ae65afe7937)
By setting decisions for the images in the batch, you can apply statuses to all the images in the batch with one click **Apply to batch**.
The next batch of the same size will be displayed, and this process will continue until all unchecked images are reviewed.

During the review process, the application allows you to modify tags for each image in the batch: text tags, numeric tags, and single-choice tags.

![](https://github.com/user-attachments/assets/27b13e2a-1770-45dc-b4b9-037fc19cd17f)

At the end of the review process, you can either set the current Labeling Job to 'Completed' status or simply proceed to the next one.
![](https://github.com/user-attachments/assets/83b8dbda-6cab-456c-9c77-b413f1973b66)

☝️ After using the app, remember to manually stop the app session in App Sessions.
