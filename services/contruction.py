import json

# Job titles to filter
FILTER_TITLES = {
    "Landscape Laborer",
    "Concrete Finisher",
    "Landscaping",
    "Welder",
    "Welder Journeyman",
    "Laborer",
    "General Construction Laborer"
}

def main():
    input_file = "data/jobs_data.json"
    output_file = "data/construction.json"

    # Load original data
    with open(input_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # Filter but keep entire object intact
    filtered_jobs = [
        job for job in jobs
        if job.get("jobTitle", "").strip() in FILTER_TITLES
    ]

    # Save full original structure for matching jobs
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(filtered_jobs, f, indent=4, ensure_ascii=False)

    print(f"{len(filtered_jobs)} jobs saved to {output_file}")

if __name__ == "__main__":
    main()
