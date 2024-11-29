from pathlib import Path
import logging

from bs4 import BeautifulSoup
from bs4.element import CData, Tag
from html_sanitizer import Sanitizer
from lxml.builder import unicode

logging.getLogger().setLevel(logging.INFO)

class ExportFormatter:
    _soup_doc: BeautifulSoup
    _soup_comments: BeautifulSoup
    _sanitizer: Sanitizer
    _comment_id: int
    _content_id: int
    _file_path: Path
    _output_folder: Path

    def __init__(self, file_path: str, output_folder: str, last_wp_id: int):
        """
        Initialize the export formatter.
        :param file_path: file to extract data from
        :param output_folder: folder to write converted data to
        :param last_wp_id: latest known WordPress database id
        """
        self._soup_comments = BeautifulSoup('<comments></comments>', 'xml')
        self._sanitizer = self._setup_sanitizer()
        self._comment_id = 0 # comments have a different increment id from posts and pages

        # user-determined values
        self._file_path = Path(file_path)
        self._output_folder = Path(output_folder)
        self._content_id = last_wp_id + 1 # set to the next id in target WP database, post and page ids will be set starting from this one

    def convert_to_wp_format(self):
        """
        Convert the content of the export file to 3 separate files in a format compatible with WordPress plugin WP All Import
        :return: Whether the process succeeded
        """
        try:
            self._soup_doc = self._load_data()
            self._clean_content('post')
            self._clean_content('page')
            self._create_files()
        except Exception as e:
            logging.error(e)
            return False
        return True

    @staticmethod
    def _setup_sanitizer():
        """
        Set sanitizer settings to allow img tags
        :return: Sanitizer instance
        """
        settings = dict(Sanitizer().__dict__)
        settings['tags'].add('img')
        settings['empty'].add('img')
        settings['attributes'].update({'img': ('src',)})
        return Sanitizer(settings=settings)

    @staticmethod
    def _check_file_structure(data: BeautifulSoup):
        """
        Check if the file structure matches the format of an OverBlog export file
        :param data: XML data from file
        :return: Whether structure is valid
        """
        if not data.posts and not data.pages:
            logging.debug("Aucun noeud 'posts' ou 'pages' trouvé")
            return False
        if data.find('origin') and (not data.find('origin').string or not 'OB' in data.find('origin').string.split(',')):
            logging.debug("Le format semble correct mais le tag 'origin' n'indique pas d'OverBlog")
            return False
        return True

    def _load_data(self):
        """
        Load the data from the file, check that the format belongs to an OverBlog export
        :return: BeautifulSoup instance of file content
        """
        if not self._file_path.exists():
            raise FileNotFoundError(f"Le fichier {self._file_path} n'existe pas")

        if not self._file_path.suffix == ".xml":
            raise ValueError("L'extension du fichier doit être .xml")

        with open(self._file_path, 'r', encoding='UTF-8') as f:
            file_content = f.read()

        xml_data = BeautifulSoup(file_content, 'xml')

        if not self._check_file_structure(xml_data):
            raise ValueError("Le format du fichier ne semble pas correspondre au format OverBlog.")

        return xml_data

    def _clean_content(self, node_name: str):
        """
        Clean the content of a node
        :param node_name: either 'post' or 'page'
        :return:
        """
        if node_name not in ('post', 'page'):
            raise NotImplementedError(f"XML Node {node_name} non supporté")

        nodes = self._soup_doc.find_all(node_name)
        logging.info(f"Formattage de {len(nodes)} {node_name}{'s' if len(nodes) > 1 else ''}...")
        for node in nodes:
            self._content_id += 1
            self._process_node(node)

    def _create_files(self):
        """
        Create the 3 resulting XML files
        :return:
        """
        Path.mkdir(self._output_folder, parents=True, exist_ok=True)

        soup_posts = self._soup_doc.posts.extract()
        self._create_file(soup=soup_posts, node_type='post', order=1)

        soup_pages = self._soup_doc.pages.extract()
        self._create_file(soup=soup_pages, node_type='page', order=2)

        self._create_file(soup=self._soup_comments, node_type='comment', order=3)

    def _create_file(self, soup: BeautifulSoup, node_type: str, order: int):
        """
        Create the XML file
        :param soup:
        :param node_type: either 'post', 'page' or 'comment'
        :param order: file order to be set in the file name
        :return:
        """
        total = len(soup.find_all(node_type))
        file_name = f"{order}_{self._file_path.stem}_{node_type}s.xml"
        logging.info(f"Sauvegarde de {total} élément{'s' if total > 1 else ''} dans le fichier {file_name}")
        with open(self._output_folder / file_name, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())

    def _process_node(self, node):
        """
        Update XML structure of passed node; it directly updates the parent BeautifulSoup object (_soup_doc)
        :param node: XML element (post or page) to update to target format
        :return:
        """
        # remove unwanted tags
        node.origin.decompose()
        node.slug.decompose()
        node.created_at.decompose()
        node.modified_at.decompose()

        # add content id
        import_id_tag = self._soup_doc.new_tag('import_id')
        import_id_tag.string = str(self._content_id)
        node.append(import_id_tag)

        # sanitize html
        self._clean_html(node)

        # process comments
        total_comments = len(node.find_all('comment'))
        if node.comments and total_comments > 0:
            logging.info(f"Récupération de {total_comments} commentaire{'s' if total_comments > 1 else ''} pour le post #{self._content_id}...")
            comments = node.comments.extract()
            self._process_comments(comments)

    def _process_comments(self, comments):
        """
        Update XML structure of comments, and save them in a separate XML document
        :param comments: Comments node coming from post, page or a parent comment
        :return:
        """
        parent_id = self._comment_id
        parent_name = comments.name

        for comment in list(comments.children):
            if type(comment) != Tag:
                continue

            self._comment_id = self._comment_id + 1
            comment = comment.extract()

            # remove unwanted tags
            if comment.status:
                comment.status.decompose()

            # add parent post id
            post_id_tag = self._soup_comments.new_tag('post_id')
            post_id_tag.string = str(self._content_id)
            comment.append(post_id_tag)

            # add comment id
            comment_id_tag = self._soup_comments.new_tag('comment_id')
            comment_id_tag.string = str(self._comment_id)
            comment.append(comment_id_tag)

            # sanitize html
            self._clean_html(comment)

            # add parent id for a reply comment
            if parent_name == 'replies':
                parent_id_tag = self._soup_comments.new_tag('parent_id')
                parent_id_tag.string = str(parent_id)
                comment.append(parent_id_tag)

            # add comment to separate object
            self._soup_comments.comments.append(comment)

            # process replies recursively
            total_replies = len(comment.find_all('comment'))
            if comment.replies:
                if total_replies > 0:
                    logging.info(f"Récupération de {total_replies} réponse{'s' if total_replies > 1 else ''} au commentaire #{self._comment_id}...")
                    replies = comment.replies.extract()
                    self._process_comments(replies)
                else:
                    comment.replies.decompose()

    def _clean_html(self, node):
        """
        Clean the HTML node using Sanitizer
            - clean up HTML fragments using a very restricted set of allowed tags and attributes
            - remove inline styles
            - normalize whitespace
            - merge adjacent tags of the same type
            - convert some tags (<span style='...'>, <b> and <i>) to either <strong> or <em>
        :param node: XML node containing HTML data to clean
        :return:
        """
        sanitized_text = self._sanitizer.sanitize(unicode(node.content.string))
        node.content.string = CData(sanitized_text)

if __name__ == '__main__':
    process = ExportFormatter(file_path="../../data/export_overblog.xml", output_folder="../../data/filegen", last_wp_id=7)
    process.convert_to_wp_format()