The goal of this project is to create an online group making system for group people of similar interests at workshops.

At the landing page, the participants enter their names. This adds their name to an internal database.

The next step take place during/after a pitching period, where the participants share their ideas. The objective of the developed tool is to identify similarities between the projects. 
In this step the participants need to  evaluate how similar their topic is to the others. They should see a list of all the participants, and they should have a slider next to the names where they can indicate similarity between a score of 1 to 5.

After everyone set their simialrity scores, we create a dissimilarity matrix:
- first we subtract all the scores from 6 (to have a dissimilarity value/distance)
- then we build the distance matrix

Then we use the MDS method to create a 2-D point projection of the distance matrix. Finally, we plot a point cloud labelled with names and show the result.
