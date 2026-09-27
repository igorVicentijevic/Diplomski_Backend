from app.semantic_grouping.grouping.decision.ProposedGroupAssigner import (
    ProposedGroupAssigner,
)
from app.semantic_grouping.grouping.decision.SemanticGroupingDecision import (
    SemanticGroupingDecision,
)


def _create_decision(
    left_article_id: str,
    right_article_id: str,
    predicted_same_event: bool,
) -> SemanticGroupingDecision:
    return SemanticGroupingDecision(
        left_article_id=left_article_id,
        right_article_id=right_article_id,
        similarity=0.9 if predicted_same_event else 0.1,
        predicted_same_event=predicted_same_event,
        is_boundary_candidate=False,
    )


def test_assign_returns_transitively_merged_groups() -> None:
    decisions = [
        _create_decision("a", "b", True),
        _create_decision("b", "c", True),
        _create_decision("c", "d", False),
        _create_decision("e", "f", True),
    ]

    groups = ProposedGroupAssigner().assign(decisions)

    members_by_group = {
        group.group_id: group.article_ids for group in groups
    }
    assert sorted(
        sorted(article_ids) for article_ids in members_by_group.values()
    ) == [["a", "b", "c"], ["e", "f"]]

    group_ids = {
        decision.proposed_group_id
        for decision in decisions
        if decision.predicted_same_event
    }
    assert group_ids == set(members_by_group)
    assert all(
        group.group_id.startswith("shadow-") for group in groups
    )


def test_assign_leaves_negative_decisions_ungrouped() -> None:
    decisions = [_create_decision("a", "b", False)]

    groups = ProposedGroupAssigner().assign(decisions)

    assert groups == []
    assert decisions[0].proposed_group_id is None


def test_assign_produces_deterministic_group_ids() -> None:
    first = ProposedGroupAssigner().assign(
        [
            _create_decision("a", "b", True),
            _create_decision("b", "c", True),
        ]
    )
    second = ProposedGroupAssigner().assign(
        [
            _create_decision("c", "b", True),
            _create_decision("b", "a", True),
        ]
    )

    assert [group.group_id for group in first] == [
        group.group_id for group in second
    ]
