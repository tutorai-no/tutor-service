#!/bin/bash
# Script to fetch GitHub Actions logs using GitHub API

# Configuration
REPO="The-TutorAI-project/aksio-backend"
BRANCH="refactor/project-structure"

# Function to get latest workflow runs
get_latest_runs() {
    echo "Fetching latest workflow runs..."
    curl -s -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
        | grep -E '"id"|"status"|"conclusion"|"name"|"created_at"' \
        | sed 's/,$//' | sed 's/"//g' | sed 's/  //g'
}

# Function to get specific run logs (requires authentication)
get_run_logs() {
    RUN_ID=$1
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "Error: GITHUB_TOKEN environment variable not set"
        echo "Please set: export GITHUB_TOKEN=your_personal_access_token"
        return 1
    fi
    
    echo "Fetching logs for run ID: $RUN_ID"
    curl -L -H "Accept: application/vnd.github.v3+json" \
        -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/logs" \
        -o "workflow_logs_$RUN_ID.zip"
}

# Function to get job details
get_job_details() {
    RUN_ID=$1
    echo "Fetching job details for run ID: $RUN_ID"
    curl -s -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/jobs" \
        | grep -E '"name"|"status"|"conclusion"|"started_at"|"completed_at"' \
        | sed 's/,$//' | sed 's/"//g' | sed 's/  //g'
}

# Main execution
case "$1" in
    runs)
        get_latest_runs
        ;;
    logs)
        if [ -z "$2" ]; then
            echo "Usage: $0 logs <run_id>"
            exit 1
        fi
        get_run_logs $2
        ;;
    jobs)
        if [ -z "$2" ]; then
            echo "Usage: $0 jobs <run_id>"
            exit 1
        fi
        get_job_details $2
        ;;
    *)
        echo "Usage: $0 {runs|logs|jobs} [run_id]"
        echo ""
        echo "Commands:"
        echo "  runs    - List latest workflow runs"
        echo "  logs    - Download logs for a specific run (requires GITHUB_TOKEN)"
        echo "  jobs    - Get job details for a specific run"
        exit 1
        ;;
esac