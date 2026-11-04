# mentoring.md: Session 6 - Strategies and policy
"""Which support strategy is actually used for a reply (spec section 11.2).

Three inputs, in order of priority:
    1. safety    - any safety flag means the fixed "Safety" reply, always
    2. requested - the user's own choice in the side panel ("Requested by you")
    3. classified - the classifier's suggestion, used when the user chose "Automatic"
Both the requested and the used strategy are stored, so the research can
compare them.
"""


def choose_strategy(requested: str | None, classified: str | None, safety_flag: str,
                    strategy_names: list[str]) -> str:
    """Return the strategy name to use for this reply."""
    if safety_flag != "none":
        return "Safety"
    if requested and requested != "Automatic" and requested in strategy_names:
        return requested  # the user's preference wins over the classifier
    if classified in strategy_names:
        return classified
    return strategy_names[0]  # default = first strategy in the file
