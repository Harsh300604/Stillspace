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
    """Return the strategy name to use for this reply.

    TODO (Session 6): finish the rules from spec section 11.2, in this order:
      1. (done) any safety flag -> "Safety"
      2. if the user requested a strategy (not None, not "Automatic") AND it is in
         strategy_names -> return the requested one (the user's preference wins)
      3. else if the classifier's strategy is in strategy_names -> return it
      4. else -> strategy_names[0] (the first strategy in the file)
    Done when: choosing "Advice" in the side panel makes the reply badge say "Advice".
    """
    if safety_flag != "none":
        return "Safety"  # already done: safety always comes first, never remove this
    # Safe placeholder until Session 6: always the first strategy in the file.
    return strategy_names[0]
