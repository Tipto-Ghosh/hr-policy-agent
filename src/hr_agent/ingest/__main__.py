from hr_agent.core.settings import get_settings
from hr_agent.ingest.ingest import run_pipeline

if __name__ == "__main__":
    settings = get_settings()
    run_pipeline(settings.data_processed_dir / "hr_policy.md")