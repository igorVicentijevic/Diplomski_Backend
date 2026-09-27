import hashlib

from app.semantic_grouping.grouping.decision.SemanticGroupingDecision import (
    SemanticGroupingDecision,
)
from app.semantic_grouping.models.ProposedArticleGroup import (
    ProposedArticleGroup,
)


class ProposedGroupAssigner:
    def assign(
        self,
        decisions: list[SemanticGroupingDecision],
    ) -> list[ProposedArticleGroup]:
        """Stamps a group id on every positive decision.

        Returns the proposed groups the decisions were merged into.
        """
        parent_map = self._build_parent_map(decisions)
        groups = self._create_groups(parent_map)
        group_by_article_id = {
            article_id: group.group_id
            for group in groups
            for article_id in group.article_ids
        }

        for decision in decisions:
            if decision.predicted_same_event:
                decision.proposed_group_id = group_by_article_id[
                    decision.left_article_id
                ]

        return groups

    def _build_parent_map(
        self,
        decisions: list[SemanticGroupingDecision],
    ) -> dict[str, str]:
        """Unions every positively linked pair into a disjoint set.

        Returns a parent map where each key is an article id and each
        value is that article's direct parent; a root points to itself.
        Transitive links are resolved here: articles that were never
        compared directly still end up under a shared root.
        """
        parent_map: dict[str, str] = {}
        for decision in decisions:
            if decision.predicted_same_event:
                self._union(
                    parent_map,
                    decision.left_article_id,
                    decision.right_article_id,
                )
        return parent_map

    def _create_groups(
        self,
        parent_map: dict[str, str],
    ) -> list[ProposedArticleGroup]:
        """Materializes the disjoint sets into explicit groups.

        Articles are collected by their root, and each set of members
        receives a deterministic group id. The root itself is not used
        as the id because it depends on the union order, while the
        sorted members do not.
        """
        members_by_root: dict[str, list[str]] = {}
        for article_id in parent_map:
            members_by_root.setdefault(
                self._find(parent_map, article_id),
                [],
            ).append(article_id)

        return [
            ProposedArticleGroup(
                group_id=self._create_group_id(members),
                article_ids=frozenset(members),
            )
            for members in members_by_root.values()
        ]

    @staticmethod
    def _create_group_id(members: list[str]) -> str:
        identity = "\0".join(sorted(members))
        return "shadow-" + hashlib.sha256(
            identity.encode("utf-8")
        ).hexdigest()[:16]

    def _union(
        self,
        parent_map: dict[str, str],
        left_id: str,
        right_id: str,
    ) -> None:
        left_root = self._find(parent_map, left_id)
        right_root = self._find(parent_map, right_id)
        if left_root != right_root:
            parent_map[right_root] = left_root

    def _find(
        self,
        parent_map: dict[str, str],
        article_id: str,
    ) -> str:
        parent_map.setdefault(article_id, article_id)
        while parent_map[article_id] != article_id:
            parent_map[article_id] = parent_map[parent_map[article_id]]
            article_id = parent_map[article_id]
        return article_id
