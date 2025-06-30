import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def summarize_and_cluster_transcript(transcript, num_clusters=5):
    """
    Summarizes transcript segments using TF-IDF and clusters them into topics.

    Args:
        transcript (list): A list of dictionaries with 'start', 'end', and 'text'.
        num_clusters (int): The number of story clusters to create.

    Returns:
        dict: A dictionary where keys are cluster IDs and values are lists of transcript segments.
    """
    if not transcript or len(transcript) < num_clusters:
        logging.warning("Transcript is too short for clustering. Returning all segments as one cluster.")
        return {0: transcript} if transcript else {}

    # Extract text for TF-IDF
    texts = [item['text'] for item in transcript]

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Cluster the vectors
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    kmeans.fit(tfidf_matrix)

    # Group segments by cluster
    clusters = {i: [] for i in range(num_clusters)}
    for i, item in enumerate(transcript):
        cluster_id = kmeans.labels_[i]
        clusters[cluster_id].append(item)
    
    logging.info(f"Clustered transcript into {num_clusters} topics.")
    return clusters

def select_story_clips(clusters, clips_per_cluster=2):
    """
    Selects the most representative clips from each cluster.

    Args:
        clusters (dict): A dictionary of clustered transcript segments.
        clips_per_cluster (int): The number of clips to select from each cluster.

    Returns:
        list: A list of selected clip segments, sorted by their original start time.
    """
    selected_clips = []
    for cluster_id, segments in clusters.items():
        if not segments:
            continue

        # Find the 'center' of the cluster (most representative segment)
        # For simplicity, we'll just pick the longest segments as they often have more content.
        segments.sort(key=lambda x: len(x['text']), reverse=True)
        
        # Select the top N clips from this cluster
        selected_clips.extend(segments[:clips_per_cluster])

    # Sort the final clips by their start time to maintain a chronological flow
    selected_clips.sort(key=lambda x: x['start'])
    
    logging.info(f"Selected {len(selected_clips)} clips to form the story.")
    return selected_clips

# Example Usage:
if __name__ == '__main__':
    # This is a dummy transcript for demonstration purposes.
    # In the pipeline, this would come from the transcribe_video function.
    sample_transcript = [
        {'start': 10, 'end': 15, 'text': 'we are talking about the new gaming mouse'},
        {'start': 20, 'end': 25, 'text': 'this mouse has a high DPI sensor'},
        {'start': 50, 'end': 55, 'text': 'now let us switch to the keyboard review'},
        {'start': 60, 'end': 65, 'text': 'this keyboard has mechanical switches'},
        {'start': 90, 'end': 95, 'text': 'I really like the feel of this gaming mouse'},
        {'start': 100, 'end': 105, 'text': 'the keyboard is also very responsive'}
    ]

    # Cluster the transcript into 2 topics (e.g., 'mouse' and 'keyboard')
    story_clusters = summarize_and_cluster_transcript(sample_transcript, num_clusters=2)

    # Select 2 clips from each topic to create a story
    final_story_clips = select_story_clips(story_clusters, clips_per_cluster=2)

    print("\n--- Clustered Segments ---")
    for cid, segs in story_clusters.items():
        print(f"\nCluster {cid}:")
        for seg in segs:
            print(f"  - {seg['text']}")

    print("\n--- Final Story Clips ---")
    for clip in final_story_clips:
        print(f"- {clip['text']} (at {clip['start']}s)")
