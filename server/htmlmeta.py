from html.parser import HTMLParser


class HtmlMetadataParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._in_title = False
        self._in_script = False
        self._in_style = False
        self._title_parts = []
        self.links = []
        self.metas = []
        self.script_srcs = []
        self.inline_script_size = 0
        self.inline_style_size = 0

    def handle_starttag(self, tag, attrs):
        lowered = tag.lower()
        attr_map = {str(key).lower(): (value or "") for key, value in attrs}
        if lowered == "title":
            self._in_title = True
            return
        if lowered == "meta":
            self.metas.append(attr_map)
            return
        if lowered == "link":
            self.links.append(attr_map)
            return
        if lowered == "script":
            src = attr_map.get("src", "").strip()
            if src:
                self.script_srcs.append(src)
                return
            self._in_script = True
            return
        if lowered == "style":
            self._in_style = True

    def handle_endtag(self, tag):
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = False
            return
        if lowered == "script":
            self._in_script = False
            return
        if lowered == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._in_script:
            self.inline_script_size += len(data)
        if self._in_style:
            self.inline_style_size += len(data)

    @property
    def title(self) -> str:
        return "".join(self._title_parts).strip()

    def meta_content(self, *names: str) -> str:
        wanted = {str(name or "").strip().lower() for name in names if str(name or "").strip()}
        for attrs in self.metas:
            key = (attrs.get("name") or attrs.get("property") or "").strip().lower()
            if key in wanted:
                return attrs.get("content", "").strip()
        return ""

    def link_attrs_by_rel(self, *tokens: str):
        wanted = {str(token or "").strip().lower() for token in tokens if str(token or "").strip()}
        for attrs in self.links:
            href = attrs.get("href", "").strip()
            if not href:
                continue
            rel_tokens = {part for part in attrs.get("rel", "").lower().split() if part}
            if rel_tokens & wanted:
                yield attrs


def parse_html_metadata(html: str) -> HtmlMetadataParser:
    parser = HtmlMetadataParser()
    parser.feed(str(html or ""))
    parser.close()
    return parser
