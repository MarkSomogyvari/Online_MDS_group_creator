# Workshop Group Finder

A web-based interactive group-making application that collects user interest similarities, processes them using Multidimensional Scaling (MDS), and visualizes the results in a 2D point cloud.

## Setup

1. Ensure you have Python 3.8+ and conda installed
2. Activate the raven environment: `conda activate raven`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `uvicorn app:app --reload --host 0.0.0.0 --port 8000`
5. Open your browser and navigate to `http://localhost:8000`

## Usage

1. Enter your name on the landing page
2. Wait for other participants to join
3. Rate other participants on a scale of 1-5 (1 = Not similar, 5 = Highly similar)
4. Submit your scores
5. When everyone has submitted, click "See Results" to view the MDS visualization

## Tech Stack

- **Backend**: Python, FastAPI, SQLite
- **Data Science**: scikit-learn, numpy, pandas
- **Frontend**: HTML5, Tailwind CSS, JavaScript, Plotly.js

## Algorithm

1. **Dissimilarity Conversion**: Convert similarity scores (1-5) to distances using `Distance = 6 - Score`
2. **Matrix Symmetrization**: Average asymmetric ratings: `D_ij = (D_i→j + D_j→i) / 2`
3. **Dimensionality Reduction**: Apply MDS with precomputed distances to get 2D coordinates

## Development

- Logged every development step in git commits
- Use `git log` to see the development history
