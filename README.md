# Multi-view for thermography

This repository is a tutorial to use multi-view for analysis of drone-base thermal images. It contains a description of the process, example code and all example example data required. It's suggested to work through this example and make it run on your computer before you try it on your own data.

## General introduction on multiview

This protocol present a pipeline to use multi-view back projection for analyzing thermal images that were taken with a drone. Compared to analyzing thermal images on orthomosaics directly, this approach allows to include effects of measurement time and viewing geometry in the analysis as well as to improve spatial correction of the measurements. Same as for the orthomosaic analysis, an orthomodel has to be created but the analysis is done on single images instead of orthomosaics by means back projection. The orthomosaic serves only as a reference to orient the single images in space for analysis.
The approach can be used to analyze thermal images that were taken during a drone mapping campaign of an agricultural plot experiments.
On one hand, this protocol improves the measurement precision of relative temperature differences of plant canopies, particularly when an uncalibrated thermal camera was used. On the other hand, it includes several additional steps compared to the simple analysis of thermal orthomosaics which makes it more time consuming.


![Example of Agisoft](Images/AgisoftExample.PNG)
*image_caption*


### Code for spatial correction in R-Package SpATS


```R
library(SpATS)
```
Example of spats model
```R
SpATS_fit <- SpATS(response = "Trait_of_Interest", random = ~ Xf + Yf + Plot_label + genotype:block_factor_names.treatment, fixed = ~ block_factor_names.treatment + block_factor_names.replication,
                       spatial = ~PSANOVA(X, Y, nseg = c(nX, nY), nest.div = c(1,1),
                       genotype = "genotype", genotype.as.random = TRUE, data = df_for_correction,
                       weights = df_for_correction$weights,
                       control = list(maxit = 100, tolerance = 1e-03, monitoring = 0))
```
