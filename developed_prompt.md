# Role & Objective
You are an expert full-stack developer and data scientist. Your task is to implement a web-based, interactive group-making application called "Workshop Group Finder". The application collects user interest similarities, processes them using a distance matrix and Multidimensional Scaling (MDS), and visualizes the results in a 2D point cloud.

# Tech Stack Requirements
- Backend: Python (FastAPI or Flask)
- Data Science Libraries: scikit-learn (for MDS), numpy, pandas
- Frontend: HTML5, Tailwind CSS, and JavaScript (using Plotly.js or D3.js for visualization)
- Database: SQLite (or an in-memory database for rapid prototyping)

# Core Application Workflow & Logic

## Step 1: Landing & Registration
- A clean landing page where participants enter their name.
- Upon submission, the name is stored in a database/state.

## Step 2: Pitching & Similarity Scoring
- A dynamic page that fetches all registered participants.
- Each logged-in participant must see a list of *all other* participants.
- Next to each name, provide an interactive slider with a discrete scale from 1 to 5 (1 = Not similar at all, 5 = Highly similar).
- A "Submit Scores" button that saves these values. Missing inputs should default to a mid-point score of 3.

## Step 3: Mathematical Transformation (Critical Logic)
When the administrator triggers the visualization, process the submitted scores on the backend exactly as follows:
1. **Dissimilarity Conversion:** Convert the 1-5 similarity scores into distances using the formula: 
   $$Distance = 6 - Score$$
   *(Resulting in a range of 1 to 5, where 1 is closest and 5 is furthest).*
2. **Matrix Symmetrization:** Because User A rating User B may differ from User B rating User A, you must symmetrize the $N \times N$ distance matrix by averaging opposing pairs:
   $$D_{ij} = \frac{D_{i \rightarrow j} + D_{j \rightarrow i}}{2}$$
   Ensure the diagonal ($D_{ii}$) is explicitly set to 0.

## Step 4: Dimensionality Reduction & Visualization
1. Pass the fully symmetric distance matrix into `sklearn.manifold.MDS` with `dissimilarity='precomputed'` to reduce the data to 2 dimensions $(X, Y)$.
2. Return the $(X, Y)$ coordinates paired with the participant names to the frontend via a JSON API.
3. Render an interactive 2D scatter plot using Plotly.js or D3.js. Points must be labeled with the participants' names on hover or persistent text.

# Expected Deliverables
1. `app.py`: The backend API handling routes for registration, score submission, and the MDS calculation layout.
2. `templates/index.html`: The main unified frontend interface (or broken down into clean components).
3. `requirements.txt`: Necessary Python dependencies.

Please write clean, well-commented, and modular code. Handle potential edge cases, such as a user not submitting ratings for everyone, by safely filling in default values before calculating the matrix.
