"""
Example usage of floating_prompts.

Run with: uv run python main.py
"""

from floating_prompts import Prompt, PromptRepository, get_session, init_db


def main() -> None:
    """Demonstrate basic prompt operations."""
    print("🗄️  Floating Prompts - Simple Prompt Storage\n")

    # Initialize database (creates tables if needed)
    print("Initializing database...")
    init_db()
    print("✅ Database ready\n")

    # Create some prompts
    with get_session() as session:
        repo = PromptRepository(session)

        # Create a summarizer prompt
        if not repo.exists("summarizer"):
            prompt = repo.create(
                name="summarizer",
                system_prompt="You are a helpful assistant that creates concise summaries.",
                user_prompt="Please summarize the following content:\n\n{content}",
            )
            print(f"Created: {prompt}")

        # Create a second version
        if not repo.exists("summarizer", version=2):
            prompt = repo.create(
                name="summarizer",
                system_prompt="You are an expert summarizer. Be concise and precise.",
                user_prompt="Summarize in 3 bullet points:\n\n{content}",
            )
            print(f"Created: {prompt}")

        # List all prompts
        print("\n📋 All prompts:")
        for p in repo.list_all():
            print(f"  - {p.name} v{p.version}")

        # Get latest version
        latest = repo.get_latest("summarizer")
        if latest:
            print(f"\n📝 Latest summarizer (v{latest.version}):")
            print(f"   System: {latest.system_prompt[:50]}...")
            print(f"   User: {latest.user_prompt[:50]}...")

            # Render with variables
            system, user = latest.render(content="Hello world!")
            print(f"\n🔄 Rendered:")
            print(f"   {user}")


if __name__ == "__main__":
    main()
