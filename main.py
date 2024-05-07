import copy
from bs4 import BeautifulSoup
from bs4.element import CData
from html_sanitizer import Sanitizer

Sanitizer.__dict__

file_path = "data/export_overblog.xml"

# Update sanitizer settings to allow img
my_settings = dict(Sanitizer().__dict__)
my_settings['tags'].add('img')
my_settings['empty'].add('img')
my_settings['attributes'].update({'img': ('src', )})

with open(file_path, "r", encoding='UTF-8') as f:
    data = f.read()

content_id = 7
comment_id = 0


soup_doc = BeautifulSoup(data, 'xml')
soup_comments = BeautifulSoup('<comments></comments>', 'xml')


def clean_html(node):
    sanitizer = Sanitizer(settings=my_settings)
    sanitized_text = sanitizer.sanitize(node.content.string)
    node.content.string = CData(sanitized_text)


def extract_comments(post_comments):
    global comment_id, content_id

    for comment in post_comments.children:
        parent_id = comment_id
        comment_id = comment_id + 1
        clone = copy.copy(comment)

        # remove unnecessary tags
        if clone.author_url:
            clone.author_url.decompose()
        if clone.author_ip:
            clone.author_ip.decompose()
        if clone.status:
            clone.status.decompose()

        # add parent post id
        post_id_tag = soup_comments.new_tag('post_id')
        post_id_tag.string = str(content_id)
        clone.append(post_id_tag)

        # add comment id
        comment_id_tag = soup_comments.new_tag('comment_id')
        comment_id_tag.string = str(comment_id)
        clone.append(comment_id_tag)

        clean_html(clone)

        # add parent date
        if comment.parent.parent and comment.parent.parent.name == 'comment':
            parent_id_tag = soup_comments.new_tag('parent_id')
            parent_id_tag.string = str(parent_id)
            clone.append(parent_id_tag)

        # add comment to separate object
        soup_comments.comments.append(clone)

        # process replies recursively
        if clone.replies:
            extract_comments(clone.replies)
            clone.replies.decompose()


def transform(element):
    element.origin.decompose()
    element.slug.decompose()
    element.created_at.decompose()
    element.modified_at.decompose()
    element.author.decompose()

    clean_html(element)

    import_id_tag = soup_doc.new_tag('import_id')
    import_id_tag.string = str(content_id)
    element.append(import_id_tag)

    if element.comments:
        comments = element.comments.extract()
        extract_comments(comments)


# clean posts
posts = soup_doc.find_all('post')
for post in posts:
    content_id += 1
    transform(post)

# clean pages
pages = soup_doc.find_all('page')
for page in pages:
    content_id += 1
    transform(page)

# save file with comments
with open('data/overblog_comments.xml', 'w', encoding="utf-8") as file_comments:
    file_comments.write(soup_comments.prettify())

# save file with pages
with open('data/overblog_pages.xml', 'w', encoding="utf-8") as file_pages:
    soup_pages = soup_doc.pages.extract()
    file_pages.write(soup_pages.prettify())

# save file with posts
with open('data/overblog_posts.xml', 'w', encoding="utf-8") as file_posts:
    soup_posts = soup_doc.posts.extract()
    file_posts.write(soup_posts.prettify())
