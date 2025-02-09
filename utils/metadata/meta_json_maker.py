import os
import json
import sys
from meta_data import fetch_movie_info, run_with_timeout

# API Key for TMDB
API_KEY = 'ff315049f0603ced165f84b648338838'

# Define paths
CACHE_FOLDER = "/data/ephemeral/home/cache"
OUTPUT_FOLDER = "movie_info"

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Iterate through JSON files in cache folder
for filename in os.listdir(CACHE_FOLDER):
    if filename.endswith(".json"):  # Process only JSON files
        json_path = os.path.join(CACHE_FOLDER, filename)
        print(f"Processing: {filename}")

        try:
            # Fetch movie information with timeout protection
            movie_title, movie_year, cast, crew = run_with_timeout(fetch_movie_info, 30, json_path, API_KEY)

            # Generate output filename (_8LrZ4NhPmk_stt_cache.json → _8LrZ4NhPmk_meta_data.json)
            output_filename = filename.replace("_stt_cache.json", "_meta_data.json")
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            # Prepare JSON data
            movie_data = {
                "title": movie_title,
                "year": movie_year,
                "cast": cast,
                "crew": crew
            }

            # Save movie information to JSON file
            with open(output_path, "w", encoding="utf-8") as out_file:
                json.dump(movie_data, out_file, indent=4, ensure_ascii=False)

            print(f"Saved: {output_filename}")

        except TimeoutError:
            print(f"Timeout occurred while processing {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("Processing completed.")
