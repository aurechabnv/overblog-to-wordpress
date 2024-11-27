from pathlib import Path
import logging

import copy
from bs4 import BeautifulSoup
from bs4.element import CData
from html_sanitizer import Sanitizer

# TODO: Faire un exécutable : auto-py-to-exe/pyinstaller

def setup_sanitizer():
    # Update sanitizer settings to allow img
    sane_settings = dict(Sanitizer().__dict__)
    sane_settings['tags'].add('img')
    sane_settings['empty'].add('img')
    sane_settings['attributes'].update({'img': ('src', )})
    return Sanitizer(settings=sane_settings)

class ExportFormatter:
    def __init__(self, in_path: str, out_folder: str, last_wp_id: int):
        """
        Initialize the export formatter.
        :param in_path: file to extract data from
        :param out_folder: folder to write converted data to
        :param last_wp_id: last wordpress database id
        """
        self.file_path = Path(in_path)
        self.out_folder = Path(out_folder)
        self.content_id = last_wp_id + 1 # set to the next id in your WP database, posts/pages/comments' ids will be set from this one
        self.comment_id = 0

        self.data = self._load_data()
        self.sanitizer = setup_sanitizer()

        self.soup_doc = BeautifulSoup(self.data, 'xml')
        self.soup_comments = BeautifulSoup('<comments></comments>', 'xml')

    def _load_data(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"File {self.file_path} does not exist")
        with open(self.file_path, "r", encoding='UTF-8') as f:
            file_content = f.read()
        return file_content

    def _clean_html(self, node):
        sanitized_text = self.sanitizer.sanitize(node.content.string)
        node.content.string = CData(sanitized_text)

    def _extract_comments(self, post_comments):
        for comment in post_comments.children:
            parent_id = self.comment_id
            self.comment_id = self.comment_id + 1
            clone = copy.copy(comment)

            # remove unnecessary tags
            if clone.author_url:
                clone.author_url.decompose()
            if clone.author_ip:
                clone.author_ip.decompose()
            if clone.status:
                clone.status.decompose()

            # add parent post id
            post_id_tag = self.soup_comments.new_tag('post_id')
            post_id_tag.string = str(self.content_id)
            clone.append(post_id_tag)

            # add comment id
            comment_id_tag = self.soup_comments.new_tag('comment_id')
            comment_id_tag.string = str(self.comment_id)
            clone.append(comment_id_tag)

            self._clean_html(clone)

            # add parent date
            if comment.parent.parent and comment.parent.parent.name == 'comment':
                parent_id_tag = self.soup_comments.new_tag('parent_id')
                parent_id_tag.string = str(parent_id)
                clone.append(parent_id_tag)

            # add comment to separate object
            self.soup_comments.comments.append(clone)

            # process replies recursively
            if clone.replies and len(clone.replies) > 0:
                logging.info(f"Extracting {len(clone.replies)} comment replies from comment #{self.comment_id}...")
                self._extract_comments(clone.replies)
                clone.replies.decompose()

    def _transform(self, element):
        element.origin.decompose()
        element.slug.decompose()
        element.created_at.decompose()
        element.modified_at.decompose()
        element.author.decompose()

        self._clean_html(element)

        import_id_tag = self.soup_doc.new_tag('import_id')
        import_id_tag.string = str(self.content_id)
        element.append(import_id_tag)

        if element.comments and len(element.comments) > 0:
            logging.info(f"Extracting {len(element.comments)} comments from post #{self.content_id}...")
            comments = element.comments.extract()
            self._extract_comments(comments)

    def clean_posts(self):
        posts = self.soup_doc.find_all('post')
        logging.info(f"Cleaning {len(posts)} posts...")
        for post in posts:
            self.content_id += 1
            self._transform(post)

    def clean_pages(self):
        pages = self.soup_doc.find_all('page')
        logging.info(f"Cleaning {len(pages)} pages...")
        for page in pages:
            self.content_id += 1
            self._transform(page)

    def create_files(self):
        Path.mkdir(self.out_folder, parents=True, exist_ok=True)

        # save file with comments
        with open(self.out_folder / '3_import_comments.xml', 'w', encoding="utf-8") as file_comments:
            file_comments.write(self.soup_comments.prettify())
        logging.info("Created comments file")

        # save file with pages
        soup_pages = self.soup_doc.pages.extract()
        with open(self.out_folder / '2_import_pages.xml', 'w', encoding="utf-8") as file_pages:
            file_pages.write(soup_pages.prettify())
        logging.info("Created pages file")

        # save file with posts
        soup_posts = self.soup_doc.posts.extract()
        with open(self.out_folder / '1_import_posts.xml', 'w', encoding="utf-8") as file_posts:
            file_posts.write(soup_posts.prettify())
        logging.info("Created posts file")

    def convert_to_wp_format(self):
        self.clean_posts()
        self.clean_pages()
        self.create_files()
        return True

if __name__ == '__main__':
    process = ExportFormatter(in_path="../../data/export_overblog.xml", out_folder="out", first_content_id=7)
    process.convert_to_wp_format()