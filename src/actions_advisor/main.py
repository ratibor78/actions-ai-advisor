"""Main entry point for Actions Advisor."""

import asyncio
import sys

from pydantic import ValidationError

from actions_advisor.config import Config
from actions_advisor.file_parser import parse_affected_files
from actions_advisor.formatter import format_analysis, write_job_summary
from actions_advisor.llm_client import LLMClient
from actions_advisor.log_fetcher import LogFetcher
from actions_advisor.preprocessor import preprocess_logs
from actions_advisor.tokens import TokenCounter


async def analyze_failure() -> int:
    """Analyze failed GitHub Actions jobs.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Load configuration
        config = Config()  # type: ignore[call-arg]
    except ValidationError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        return 1

    print("🔍 Actions Advisor starting...")
    print(f"📋 Repository: {config.github_repository}")
    print(f"🔢 Run ID: {config.github_run_id}")
    print(f"🤖 Provider: {config.provider} ({config.model})")

    try:
        # Fetch failed job logs
        print("\n📥 Fetching failed job logs...")
        fetcher = LogFetcher(
            github_token=config.github_token,
            repo=config.github_repository,
            run_id=config.github_run_id,
        )
        failed_jobs = await fetcher.fetch_failed_jobs()

        if not failed_jobs:
            print("✅ No failed jobs found!")
            return 0

        print(f"Found {len(failed_jobs)} failed job(s)")

        # Initialize LLM client and token counter
        llm_client = LLMClient(
            provider=config.provider,
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
        )
        token_counter = TokenCounter(config.model)

        # Process each failed job
        for i, job_log in enumerate(failed_jobs, 1):
            print(f"\n[{i}/{len(failed_jobs)}] Analyzing: {job_log.job_name} → {job_log.step_name}")

            # Preprocess logs
            preprocessed = preprocess_logs(job_log.raw_logs)
            print(f"  📉 Preprocessed logs: {len(job_log.raw_logs)} → {len(preprocessed)} chars")

            # Parse affected files from logs (gracefully handle failures)
            affected_files = []
            try:
                affected_files = parse_affected_files(job_log.raw_logs)
                if affected_files:
                    print(f"  📁 Found {len(affected_files)} affected file(s)")
            except Exception as e:
                # Don't fail the entire analysis if file parsing fails
                print(f"  ⚠️  File parsing failed: {e}", file=sys.stderr)

            # Count tokens
            token_count = token_counter.count_tokens(preprocessed)
            print(f"  🔢 Estimated input tokens: {token_count}")

            # Analyze with LLM
            print("  🤖 Sending to LLM for analysis...")
            try:
                result = await llm_client.analyze(job_log, preprocessed)
                print(f"  ✅ Analysis complete ({result.output_tokens} output tokens)")

                # Estimate cost
                estimated_cost = TokenCounter.estimate_cost(
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    provider=config.provider,
                    model=config.model,
                )

                # Format and write output
                markdown = format_analysis(
                    job_log,
                    result,
                    estimated_cost,
                    affected_files=affected_files,
                    repo_owner=config.repo_owner,
                    repo_name=config.repo_name,
                    commit_sha=config.github_sha,
                )
                write_job_summary(markdown)

                if estimated_cost is not None:
                    print(f"  💰 Estimated cost: ${estimated_cost:.4f}")

            except Exception as e:
                print(f"  ⚠️  LLM analysis failed: {e}", file=sys.stderr)
                # Continue with other jobs even if one fails
                continue

        print("\n✅ Analysis complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main() -> None:
    """Entry point for the CLI."""
    exit_code = asyncio.run(analyze_failure())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
