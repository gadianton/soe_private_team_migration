import logging
from so4t_api import StackClient


class MigrationClient(object):

    def __init__(self, url: str, main_token: str, main_key: str, private_team: str,
                 private_token: str, backup_account_id: int = -1,
                 proxy_url: str = None, ssl_verify: bool = True):

        self.main_team = StackClient(url, main_token, key=main_key, ssl_verify=ssl_verify,
                                     proxy=proxy_url)
        self.private_team = StackClient(url, private_token, private_team=private_team,
                                        ssl_verify=ssl_verify, proxy=proxy_url)

        self.backup_account_id = backup_account_id
        logging.info(f"Backup account ID was set to {self.backup_account_id}")

    def copy_question_from_private_to_main(self, question_id: int):

        original_question = self.private_team.get_question_by_id(question_id)
        logging.info(f"Original Question Owner is {original_question['owner']}")
        self.set_impersonation_token(original_question['owner'])

        title = original_question['title']
        body = original_question['body']
        tags = [tag['name'] for tag in original_question['tags']]

        content_type = "question"
        log_start_of_copy(content_type, original_question['shareUrl'])
        new_question = self.main_team.add_question(title, body, tags, impersonation=True)
        log_end_of_copy(content_type, new_question['shareUrl'])

        original_answers = self.private_team.get_answers(question_id)
        content_type = "answer"
        for original_answer in original_answers:
            self.set_impersonation_token(original_answer['owner'])
            body = original_answer['body']

            log_start_of_copy(content_type, original_answer['shareLink'])
            new_answer = self.main_team.add_answer(new_question['id'], body, impersonation=True)
            log_end_of_copy(content_type, new_answer['shareLink'])

    def copy_all_questions_from_private_to_main(self):

        questions = self.private_team.get_questions()
        for question in questions:
            self.copy_question_from_private_to_main(question['id'])

    def copy_article_from_private_to_main(self, article_id: int):

        original_article = self.private_team.get_article_by_id(article_id)
        self.set_impersonation_token(original_article['owner'])

        title = original_article['title']
        body = original_article['body']
        tags = [tag['name'] for tag in original_article['tags']]
        article_type = original_article['type']

        content_type = "article"
        log_start_of_copy(content_type, original_article['shareUrl'])
        new_article = self.main_team.add_article(
            title, body, article_type, tags, impersonation=True)
        log_end_of_copy(content_type, new_article['shareUrl'])

    def copy_all_articles_from_private_to_main(self):

        articles = self.private_team.get_articles()
        for article in articles:
            self.copy_article_from_private_to_main(article['id'])

    def set_impersonation_token(self, user):

        try:
            account_id = user['accountId']
        except TypeError:  # If user has been deleted, the value will be None
            account_id = self.backup_account_id

        logging.info(f"Setting impersonation token for account ID: {account_id}")
        self.main_team.impersonation_token = self.main_team.get_impersonation_token(account_id)


def log_start_of_copy(content_type, url):

    logging.info(f"Copying {content_type} at this URL: {url}")


def log_end_of_copy(content_type, url):

    logging.info(f"{content_type.capitalize()} copied to this URL: {url}")
