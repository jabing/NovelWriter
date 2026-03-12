# src/llm/trinity_router_example.py
"""Example usage of Trinity Model Router with user's actual configuration.

This demonstrates how to use the GLM Coding Plan + Infini AI setup.
"""

from typing import Any

from src.llm.trinity_config import (
    GENRE_CONFIG,
    TRINITY_MODELS,
    USER_PROVIDERS,
)


class TrinityRouter:
    """Working router using user's actual Infini AI + Zhipu setup."""

    def __init__(self):
        self.providers = USER_PROVIDERS
        self.models = TRINITY_MODELS
        self.usage_stats = {
            "kimi-k2.5": {"tokens": 0, "cost": 0.0, "chapters": 0},
            "deepseek-v3": {"tokens": 0, "cost": 0.0, "chapters": 0},
            "deepseek-r1": {"tokens": 0, "cost": 0.0, "chapters": 0},
            "glm-5": {"tokens": 0, "cost": 0.0, "chapters": 0},
        }

    def route_chapter(
        self,
        chapter_number: int,
        total_chapters: int,
        genre: str = "fantasy",
        chapter_description: str = "",
    ) -> dict[str, Any]:
        """Route chapter to appropriate model.

        Returns dict with:
        - model: Which model to use
        - provider: Which provider config to use
        - model_id: The actual model ID for the API
        - temperature: Recommended temperature
        - estimated_cost: Cost for this chapter
        - reasoning: Why this model was chosen
        """

        # Determine chapter type
        chapter_type = self._classify_chapter(chapter_number, total_chapters, chapter_description)

        # Get genre config
        genre_cfg = GENRE_CONFIG.get(genre.lower(), GENRE_CONFIG["fantasy"])

        # Route based on chapter type and genre
        if chapter_type in ["golden", "elite", "climax", "finale"]:
            model_key = genre_cfg["elite_model"]
            reasoning = f"{chapter_type.upper()}: Highest quality required for reader engagement"

        elif chapter_type == "reasoning" or "mystery" in genre.lower():
            model_key = "deepseek-r1"
            reasoning = "REASONING: Complex logic/plot requires R1"

        elif chapter_type == "worldbuilding":
            model_key = "glm-5"
            reasoning = "WORLDBUILDING: GLM-5 excels at architecture (no extra cost)"

        else:
            model_key = genre_cfg["standard_model"]
            reasoning = "STANDARD: Cost-effective quality for daily chapters"

        # Get model config
        model_cfg = self.models[model_key]
        provider_name = model_cfg["provider"]
        provider_cfg = self.providers[provider_name]

        # Get actual model ID for API
        model_id = model_key
        if provider_cfg.models and model_key in provider_cfg.models:
            model_id = model_key  # Infini uses same IDs
        elif model_key == "glm-5":
            model_id = "glm-5"  # Zhipu official

        # Calculate cost
        tokens_est = 3000  # Average chapter
        cost = (tokens_est / 1000) * model_cfg["cost_per_1k_tokens"]

        return {
            "model_key": model_key,
            "model_name": model_cfg["name"],
            "provider": provider_name,
            "provider_type": provider_cfg.provider_type,
            "model_id": model_id,  # For API calls
            "api_key": provider_cfg.api_key,
            "base_url": provider_cfg.base_url,
            "temperature": model_cfg["temperature_recommended"],
            "max_tokens": 4000,
            "estimated_cost": round(cost, 3),
            "reasoning": reasoning,
            "chapter_type": chapter_type,
            "is_fixed_cost": model_cfg["cost_per_1k_tokens"] == 0.0,
        }

    def _classify_chapter(self, chapter_num: int, total: int, description: str) -> str:
        """Classify chapter type."""
        # Golden chapters
        if chapter_num <= 3:
            return "golden"

        # Volume starts (every 50)
        if chapter_num > 3 and chapter_num % 50 == 1:
            return "elite"

        # Climax zone (85-95%)
        progress = chapter_num / total
        if 0.85 <= progress <= 0.95:
            return "climax"
        if progress > 0.95:
            return "finale"

        # Check description
        desc_lower = description.lower()
        if any(word in desc_lower for word in ["world", "system", "design", "architecture"]):
            return "worldbuilding"
        if any(word in desc_lower for word in ["mystery", "clue", "reveal", "twist"]):
            return "reasoning"
        if any(word in desc_lower for word in ["climax", "peak", "emotional", "confession"]):
            return "elite"

        return "standard"

    def generate_full_plan(self, total_chapters: int, genre: str) -> list[dict]:
        """Generate routing plan for entire novel."""
        plan = []

        for ch in range(1, total_chapters + 1):
            route = self.route_chapter(ch, total_chapters, genre)
            plan.append({
                "chapter": ch,
                "model": route["model_name"],
                "type": route["chapter_type"],
                "cost": route["estimated_cost"],
                "reason": route["reasoning"],
            })

        return plan

    def print_cost_summary(self, total_chapters: int, genre: str):
        """Print cost summary."""
        print(f"\n{'='*60}")
        print("Trinity Model Router - Cost Estimate")
        print(f"{'='*60}")
        print(f"Novel: {total_chapters} chapters, Genre: {genre}")
        print("Providers: Zhipu Coding Plan + Infini AI")
        print(f"{'='*60}\n")

        # Generate plan
        plan = self.generate_full_plan(total_chapters, genre)

        # Count by model
        model_counts = {}
        total_cost = 0.0

        for p in plan:
            model = p["model"]
            cost = p["cost"]

            if model not in model_counts:
                model_counts[model] = {"chapters": 0, "cost": 0.0}

            model_counts[model]["chapters"] += 1
            model_counts[model]["cost"] += cost
            total_cost += cost

        # Print breakdown
        for model, data in model_counts.items():
            print(f"{model}:")
            print(f"  Chapters: {data['chapters']}")
            print(f"  Cost: ¥{data['cost']:.2f}")
            if data['cost'] == 0.0:
                print("  Note: Covered by Coding Plan")
            print()

        print(f"{'='*60}")
        print(f"Total Variable Cost: ¥{total_cost:.2f}")
        print(f"Cost per Chapter (avg): ¥{total_cost/total_chapters:.3f}")

        # Compare to all-Kimi
        all_kimi_cost = total_chapters * 0.045
        savings = all_kimi_cost - total_cost
        print(f"Savings vs All-Kimi: ¥{savings:.2f} ({savings/all_kimi_cost*100:.0f}%)")
        print(f"{'='*60}\n")


# Example usage
if __name__ == "__main__":
    router = TrinityRouter()

    # Example 1: Route a single chapter
    print("Example 1: Route Chapter 1 (Golden)")
    print("-" * 60)
    route = router.route_chapter(
        chapter_number=1,
        total_chapters=100,
        genre="romance",
        chapter_description="Opening chapter with emotional hook"
    )
    print(f"Model: {route['model_name']}")
    print(f"Provider: {route['provider']} ({route['provider_type']})")
    print(f"Model ID: {route['model_id']}")
    print(f"API Key: {route['api_key'][:10]}...")
    print(f"Base URL: {route['base_url']}")
    print(f"Temperature: {route['temperature']}")
    print(f"Estimated Cost: ¥{route['estimated_cost']}")
    print(f"Reason: {route['reasoning']}")
    print()

    # Example 2: Route an outline
    print("Example 2: Route Outline Creation")
    print("-" * 60)
    route = router.route_chapter(
        chapter_number=0,  # Outline
        total_chapters=100,
        genre="fantasy",
        chapter_description="Worldbuilding and magic system design"
    )
    print(f"Model: {route['model_name']}")
    print(f"Cost: ¥{route['estimated_cost']} (Fixed by Coding Plan!)")
    print(f"Reason: {route['reasoning']}")
    print()

    # Example 3: Full novel cost estimate
    print("Example 3: Full Novel Cost Estimate")
    router.print_cost_summary(100, "fantasy")

    # Example 4: Romance novel (more Kimi usage)
    print("Example 4: Romance Novel (More Elite Chapters)")
    router.print_cost_summary(100, "romance")
