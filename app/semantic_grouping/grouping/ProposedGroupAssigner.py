import hashlib

from app.semantic_grouping.models.SemanticGroupingDecision import (
    SemanticGroupingDecision,
)


class ProposedGroupAssigner:
    def assign(
        self,
        decisions: list[SemanticGroupingDecision],
    ) -> None:
        parent = self._build_parent_map(decisions)
        group_by_article_id = self._create_group_ids(parent)

        for decision in decisions:
            if decision.predicted_same_event:
                decision.proposed_group_id = group_by_article_id[
                    decision.left_article_id
                ]

    def _build_parent_map(
        self,
        decisions: list[SemanticGroupingDecision],
    ) -> dict[str, str]:
        parent: dict[str, str] = {}
        for decision in decisions:
            if decision.predicted_same_event:
                self._union(
                    parent,
                    decision.left_article_id,
                    decision.right_article_id,
                )
        return parent

    def _create_group_ids(
        self,
        parent: dict[str, str],
    ) -> dict[str, str]:
        members_by_root: dict[str, list[str]] = {}
        for article_id in parent:
            members_by_root.setdefault(
                self._find(parent, article_id),
                [],
            ).append(article_id)

        group_by_article_id: dict[str, str] = {}
        for members in members_by_root.values():
            group_id = self._create_group_id(members)
            for article_id in members:
                group_by_article_id[article_id] = group_id
        return group_by_article_id

    @staticmethod
    def _create_group_id(members: list[str]) -> str:
        identity = "\0".join(sorted(members))
        return "shadow-" + hashlib.sha256(
            identity.encode("utf-8")
        ).hexdigest()[:16]

    def _union(
        self,
        parent: dict[str, str],
        left_id: str,
        right_id: str,
    ) -> None:
        left_root = self._find(parent, left_id)
        right_root = self._find(parent, right_id)
        if left_root != right_root:
            parent[right_root] = left_root

    def _find(
        self,
        parent: dict[str, str],
        article_id: str,
    ) -> str:
        parent.setdefault(article_id, article_id)
        while parent[article_id] != article_id:
            parent[article_id] = parent[parent[article_id]]
            article_id = parent[article_id]
        return article_id
