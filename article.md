# Intro
This article and program is made as a final exam for rubythalib.ai computer vision superclass, also for improving SCCR's stem cell production process.

# Background - Stem Cell Production
Stem cell is a very powerful cells that can replicate and morph into any human cells that the body needs. Stem cell therapy is a medical procedure to introduce pluripotent stem cell into a human body through intravenous or injection to direct site. Most medications aim to prevent, or cure the sickness; stem cell therapy aims to cure, prevent and regenerate, all at the same time. Damaged organs are restored to its normal state, functioning like nothing happened.

# Problem 
Growing cells in the laboratory is known as “cell culture.” Stem cells can proliferate in laboratory environments in a culture dish that contains a nutrient broth known as culture medium. Most stem cells attach, divide, and spread over the surface of the dish.

The culture dish becomes crowded as the cells divide, so they need to be re-plated in the process of subculturing, which is repeated periodically many times over many months. Each cycle of subculturing is referred to as a “passage.” 

Determining when to add more nutrients, subculture, and other actions depends on several variables. One of the variable is cell confluency. Confluency represents the percentage of a culture vessel's surface area covered by the stem cell.

The current problem is to determine confluency, we simply eyeball it manually. This is inaccurate due to human perception subjectivity. The other solution is to use a microscope and pay for their proprietary software. Existing open source solutions are not robust enough to generalize cell confluency across multiple kinds of cells, including pluripotent stem cells.

# Method - Cellpose
## Overview
Cellpose is a cell and nucleus segmentation model with superhuman generalization. It can be optimized for your own data regardless of cell shape, cell size, image quality and channel order.

Cellpose actually does MORE than binary masking, it does instance segmentation, which means we can count how many cells in a dish with extreme precision.

## Output
The Cellpose neural network is designed to predict three distinct spatially-registered maps for every input image. This multi-task learning framework forces the network to learn a richer representation of cellular features than a simple binary classifier would. 

Cellpose will use all of these 3 outputs to calculate the final instance segmentation:

1. **channel 0 - horizontal flow**, Defines the gradient of the topological map in the x-direction. Directs pixels left/right toward the cell center.
2. **channel 1 - vertical flow**, Defines the gradient of the topological map in the y-direction. Directs pixels up/down toward the cell center.
3. **channel 2 - Cell probability**,  pixel-wise logit map indicating the likelihood that a pixel belongs to *any* cell. Acts as the background filter.

However, because we're only calculating cell probability, we don't need to delve into the simulation and instantiation. Cellpose is extremely fascinating work, i suggest you read the full paper [here](https://pubmed.ncbi.nlm.nih.gov/33318659/).

## Parameters
setting the correct parameter value is crucial for confluency accuracy. Check the full definition of each parameters [here](https://cellpose.readthedocs.io/en/latest/settings.html)
**Cell diameter**, i set this to **50** or **55** pixels when using 4x zoom microscope.  
**Flow threshold**, pluripotent stem cells are shaped like spindles, therefore irregular. i set this to **2** to combat the irregularity.  
**cellprob threshold**, decides how much part of cells are included in the binary mask. setting it to 0 usually causes the cell walls to be excluded. anything between **-0.5** to **-2** is good.  
**n_iteration / niter**, how many times to run simulation. irregular cell shapes demands higher niter value. i set this to **2000**. 

## Results
cellpose managed to yield good accuracy up to 60-70% confluency. Beyond that, accuracy drops dramatically due to huge parts of the image not being segmented at all.

This could happen due two things.

First, the cells are incredibly packed in large areas, like a brick. This makes instantiating the cell walls very difficult. So the model treat this as one big cell, which will exceed the cell diameter parameter, thus excluding it from the segmentation.

Second, the tightly packed cells are especially prone to lighting artifacts. Parts where cells are correctly exposed yields good results. Other parts that doesnt have the same exposure just vanishes from the segmentation.

One potential solution is to improve initial image capture and applying preprocessing to even out the exposure. Another solution is to use a different model based on newer architecture, like transformer architecture.

Despite not having perfect accuracy across all confluency levels, i believe the app is still very helpful because it can act as a base for estimation. When operators use the app, they can see the segmentation result. If the app says confluency is 68%, but parts of the stem cells are not segmented, then the actual confluency must be above 68%.

# Data Collection
Stem cell images are collected from SCCR stem cell labs, not a public domain data. There are reports that changing the serum/nutrient will change the shape of the stem cells. However, we can simply update the parameters to combat this problem.

# Data Training
To generate the cell probability map, cellpose utilizes the ResNet architecture. This model is trained on a dataset of over 70,000 segmented objects across varied image modalities. Crucially, this dataset relies on human annotation, which cellpose innately facilitates.

for our use case, which is detecting confluency up to 50%, the cellpose generalist model is good enough and can be used as is, with the correct parameters of course. 

However for use cases upwards of 80% confluency, cellpose still needs a lot of improvements. For now, we're still in the planning phase.

# Model Serving/Inference
the model/app is installed in the operators' workplace. When an image of the stem cell culture is captured, the operator will load the image to the app, run the segmentation, and get the confluency number.

I have prepared a script to batch process all image in one folder. It also outputs a text report and the resulting images.

# Closing Thoughts
rubythalib.ai computer vision superclass has taught me a lot about computer vision, starting from the basic, all the way to the advanced. Implementing this project taught me even more about real life challenges to get a good model accuracy. Hopefully you, dear reader, is benefitted in some way after reading this article. thank you. 
