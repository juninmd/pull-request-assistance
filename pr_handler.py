class PRHandler:
    def __init__(self):
        self.target_author = "Jules da Google"

    def is_target_author(self, author):
        return author == self.target_author

    def has_conflicts(self, pr_details):
        return pr_details.get('has_conflicts', False)

    def is_pipeline_successful(self, pr_details):
        return pr_details.get('pipeline_status') == 'success'

    def decide_action(self, pr_details):
        """
        Decides the action to take based on PR details.
        Returns: One of "IGNORE", "RESOLVE_CONFLICTS", "REQUEST_CORRECTIONS", "AUTO_MERGE"
        """
        if not self.is_target_author(pr_details.get('author')):
            return "IGNORE"

        if self.has_conflicts(pr_details):
            return "RESOLVE_CONFLICTS"

        if not self.is_pipeline_successful(pr_details):
            return "REQUEST_CORRECTIONS"

        return "AUTO_MERGE"
