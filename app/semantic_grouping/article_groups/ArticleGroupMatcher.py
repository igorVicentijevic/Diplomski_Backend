from app.semantic_grouping.models.ArticleGroupModel import ArticleGroupModel


class ArticleGroupMatcher:
    def match(
        self,
        proposed_groups: dict[str, set[str]],
        groups: list[ArticleGroupModel],
        memberships: dict[str, set[str]],
    ) -> dict[str, ArticleGroupModel]:
        candidates = self._create_candidates(
            proposed_groups,
            groups,
            memberships,
        )
        return self._select_matches(candidates)

    @staticmethod
    def _create_candidates(
        proposed_groups: dict[str, set[str]],
        groups: list[ArticleGroupModel],
        memberships: dict[str, set[str]],
    ) -> list[tuple[int, int, str, str, ArticleGroupModel]]:
        candidates: list[
            tuple[int, int, str, str, ArticleGroupModel]
        ] = []
        for proposed_group_id, proposed_article_ids in proposed_groups.items():
            for group in groups:
                overlap = len(
                    proposed_article_ids & memberships.get(group.id, set())
                )
                if overlap:
                    candidates.append(
                        (
                            -overlap,
                            -int(group.active),
                            proposed_group_id,
                            group.id,
                            group,
                        )
                    )
        return candidates

    @staticmethod
    def _select_matches(
        candidates: list[
            tuple[int, int, str, str, ArticleGroupModel]
        ],
    ) -> dict[str, ArticleGroupModel]:
        matches: dict[str, ArticleGroupModel] = {}
        matched_group_ids: set[str] = set()
        for _, _, proposed_group_id, group_id, group in sorted(candidates):
            if (
                proposed_group_id not in matches
                and group_id not in matched_group_ids
            ):
                matches[proposed_group_id] = group
                matched_group_ids.add(group_id)
        return matches
