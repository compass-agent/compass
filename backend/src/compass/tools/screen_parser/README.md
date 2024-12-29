# Experiment 1: OmniParser and YOLO Relationship - Key Concepts

The objective of this experiment is to understand if we can improve the coordinate suggestion of the Sonnet 3.5 model.

## Problem

Currently, Sonnet 3.5 is not performing well in understanding the coordinates of GUI elements on the screen. This can be seen in the SingleTest folder, where Sonnet 3.5 was unable to identify the correct coordinates for the Slack icon and failed to recognize icons near it.

## Proposed Solution

We propose enhancing screenshot processing for Sonnet 3.5 by:
1. Extracting icons from the screenshot
2. Captioning these icons
3. Feeding this enhanced information to Sonnet 3.5

This particular experiment aims to answer:
1. Can we effectively extract icons from screenshots?
2. Can we generate accurate captions for these icons?

### Progress on Icon Extraction

We are using:
- A Microsoft-finetuned version of YOLO for icon detection
- An OCR model for text extraction
- A combination system to merge results and handle overlaps

Results: The system shows promising performance with acceptable latency (under 1000ms). 
You can see the results of overlapped detected icons and text in the `imgs/last_image_annotated.png` file. 

### Progress on Icon Captioning

We tested the BLIP2 model for captioning. However:
- Requires significant GPU memory
- Even with 24GB memory on M3 Mac, processing was very slow
- First version took 5 minutes per screen with suboptimal results


Although, there are chance to solve this problem, I am not sure if its the easier way to solve this problem. 

## Next Steps
Before going deeper in the captioning model, I want to try a more normal path. Can we consider using Haiku in batch mode for this captioning task? 

   - Estimated cost: under 1 cent per screenshot
   How: Image to Token: pixel * pixel / 750 
   So for an small icon of 100x100, it will be 100*100/750 = 13 tokens
   Haiku 3.5 cost per input / output 1M token is 0.8$ and 4$ respectively. 
   Assuming system prompt of 100 tokens (90% cost drop with caching) + 13 tokents per image and having max of 10 tokens per output, and assuming to have 100 icons per page, the cost will be ((10+13)*0.8 + 10 * 4) * = 0.0058$
   - Server-side processing enables easy scaling and parallelization


