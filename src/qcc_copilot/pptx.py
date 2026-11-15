from __future__ import annotations

import zipfile
from xml.sax.saxutils import escape

# 仅用标准库生成真实、可打开、文字/表格可编辑的 PPTX（OOXML 包）。
# 生成器与渲染器分离：本模块只负责编译文件，不把"文件存在"当作渲染检查通过。
_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
_RT = _R + "/"

NS = f'xmlns:a="{_A}" xmlns:r="{_R}" xmlns:p="{_P}"'

EMU_W, EMU_H = 12192000, 6858000


def _esc(text) -> str:
    return escape(str(text))


def _text_shape(sid, name, x, y, cx, cy, paragraphs, *, size=1800, bold=False, color="222222"):
    paras = []
    for text in paragraphs:
        paras.append(
            f'<a:p><a:pPr marL="285750" indent="-285750"/>'
            f'<a:r><a:rPr lang="zh-CN" sz="{size}" b="{1 if bold else 0}" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr>'
            f'<a:t>{_esc(text)}</a:t></a:r></a:p>'
        )
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{_esc(name)}"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720"/>'
        f'<a:lstStyle/>{"".join(paras)}</p:txBody></p:sp>'
    )


def _table_shape(sid, x, y, cx, cy, table):
    cols = table.get("columns", [])
    rows = table.get("rows", [])
    ncol = max(1, len(cols))
    colw = cx // ncol
    grid = "".join(f'<a:gridCol w="{colw}"/>' for _ in range(ncol))
    trs = []
    rowh = 370000
    for row in rows:
        cells = []
        for val in row:
            cells.append(
                '<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>'
                f'<a:p><a:r><a:rPr lang="zh-CN" sz="1400"/>'
                f'<a:t>{_esc(val)}</a:t></a:r></a:p></a:txBody></a:tc>'
            )
        trs.append(f'<a:tr h="{rowh}">{"".join(cells)}</a:tr>')
    return (
        f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{sid}" name="数据表"/>'
        f'<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/>'
        f'</p:nvGraphicFramePr><p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
        f'<a:graphic><a:graphicData uri="{_A}/table"><a:tbl><a:tblPr firstRow="1" bandRow="1">'
        f'<a:tableStyleId>{{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}}</a:tableStyleId></a:tblPr>'
        f'<a:tblGrid>{grid}</a:tblGrid>{"".join(trs)}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>'
    )


def _group_sppr():
    return (
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
        '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
    )


def _slide_xml(title, bullets, table):
    shapes = [
        _text_shape(2, "标题", 457200, 274320, 11277600, 900000, [title],
                    size=3200, bold=True, color="1F3864")
    ]
    if table:
        shapes.append(_table_shape(4, 457200, 1500000, 11277600, 4500000, table))
    elif bullets:
        shapes.append(
            _text_shape(3, "正文", 457200, 1400000, 11277600, 5000000,
                        [("• " + str(b)) for b in bullets], size=1800)
        )
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:sld {NS}><p:cSld><p:spTree>{_group_sppr()}{"".join(shapes)}</p:spTree></p:cSld>'
        f'<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
    )


def _slide_rels():
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{_RELS}">'
        f'<Relationship Id="rId1" Type="{_RT}slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
        f'</Relationships>'
    )


class Presentation:
    def __init__(self, title="QCC 课题成果"):
        self.title = title
        self.slides = []

    def add_slide(self, title, bullets=None, table=None):
        self.slides.append({"title": title, "bullets": bullets or [], "table": table})
        return self

    def build(self):
        n = len(self.slides)
        parts = {}
        parts["[Content_Types].xml"] = _content_types(n)
        parts["_rels/.rels"] = _root_rels()
        parts["docProps/core.xml"] = _core(self.title)
        parts["docProps/app.xml"] = _app(n)
        parts["ppt/presentation.xml"] = _presentation(n)
        parts["ppt/_rels/presentation.xml.rels"] = _presentation_rels(n)
        parts["ppt/presProps.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentationPr {NS}/>'
        parts["ppt/viewProps.xml"] = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:viewPr {NS}/>'
        parts["ppt/tableStyles.xml"] = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<a:tblStyleLst xmlns:a="{_A}" def="{{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}}"/>'
        )
        parts["ppt/slideMasters/slideMaster1.xml"] = _slide_master()
        parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = _slide_master_rels()
        parts["ppt/slideLayouts/slideLayout1.xml"] = _slide_layout()
        parts["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = _slide_layout_rels()
        parts["ppt/theme/theme1.xml"] = _theme()
        for i, s in enumerate(self.slides, start=1):
            parts[f"ppt/slides/slide{i}.xml"] = _slide_xml(s["title"], s["bullets"], s["table"])
            parts[f"ppt/slides/_rels/slide{i}.xml.rels"] = _slide_rels()
        return parts

    def save(self, path):
        import os

        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in self.build().items():
                z.writestr(name, data.encode("utf-8"))
        return path


def _content_types(n):
    PML = "application/vnd.openxmlformats-officedocument.presentationml."
    overrides = [
        ("/ppt/presentation.xml", PML + "presentation.main+xml"),
        ("/ppt/presProps.xml", PML + "presProps+xml"),
        ("/ppt/viewProps.xml", PML + "viewProps+xml"),
        ("/ppt/tableStyles.xml", PML + "tableStyles+xml"),
        ("/ppt/slideMasters/slideMaster1.xml", PML + "slideMaster+xml"),
        ("/ppt/slideLayouts/slideLayout1.xml", PML + "slideLayout+xml"),
        ("/ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
        ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml"),
    ]
    for i in range(1, n + 1):
        overrides.append((f"/ppt/slides/slide{i}.xml", PML + "slide+xml"))
    ov = "".join(f'<Override PartName="{p}" ContentType="{c}"/>' for p, c in overrides)
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Types xmlns="{_CT}">'
        f'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        f'<Default Extension="xml" ContentType="application/xml"/>'
        f'{ov}</Types>'
    )


def _root_rels():
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{_RELS}">'
        f'<Relationship Id="rId1" Type="{_RT}officeDocument" Target="ppt/presentation.xml"/>'
        f'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        f'<Relationship Id="rId3" Type="{_RT}extended-properties" Target="docProps/app.xml"/>'
        f'</Relationships>'
    )


def _presentation(n):
    sld = "".join(f'<p:sldId id="{255 + i}" r:id="rId{1 + i}"/>' for i in range(1, n + 1))
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:presentation {NS} saveSubsetFonts="1">'
        f'<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        f'<p:sldIdLst>{sld}</p:sldIdLst>'
        f'<p:sldSz cx="{EMU_W}" cy="{EMU_H}" type="screen16x9"/>'
        f'<p:notesSz cx="6858000" cy="9144000"/></p:presentation>'
    )


def _presentation_rels(n):
    rels = [f'<Relationship Id="rId1" Type="{_RT}slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(1, n + 1):
        rels.append(f'<Relationship Id="rId{1 + i}" Type="{_RT}slide" Target="slides/slide{i}.xml"/>')
    rid = 2 + n
    rels.append(f'<Relationship Id="rId{rid}" Type="{_RT}presProps" Target="presProps.xml"/>')
    rels.append(f'<Relationship Id="rId{rid + 1}" Type="{_RT}viewProps" Target="viewProps.xml"/>')
    rels.append(f'<Relationship Id="rId{rid + 2}" Type="{_RT}theme" Target="theme/theme1.xml"/>')
    rels.append(f'<Relationship Id="rId{rid + 3}" Type="{_RT}tableStyles" Target="tableStyles.xml"/>')
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{_RELS}">{"".join(rels)}</Relationships>'
    )


def _slide_master():
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:sldMaster {NS}><p:cSld><p:spTree>{_group_sppr()}</p:spTree></p:cSld>'
        f'<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
        f'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
        f'<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
        f'</p:sldMaster>'
    )


def _slide_master_rels():
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{_RELS}">'
        f'<Relationship Id="rId1" Type="{_RT}slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
        f'<Relationship Id="rId2" Type="{_RT}theme" Target="../theme/theme1.xml"/>'
        f'</Relationships>'
    )


def _slide_layout():
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="空白"><p:spTree>{_group_sppr()}'
        f'</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'
    )


def _slide_layout_rels():
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{_RELS}">'
        f'<Relationship Id="rId1" Type="{_RT}slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
        f'</Relationships>'
    )


def _theme():
    colors = [
        ("dk1", '<a:sysClr val="windowText" lastClr="000000"/>'),
        ("lt1", '<a:sysClr val="window" lastClr="FFFFFF"/>'),
        ("dk2", '<a:srgbClr val="1F3864"/>'),
        ("lt2", '<a:srgbClr val="EEECE1"/>'),
        ("accent1", '<a:srgbClr val="2E75B6"/>'),
        ("accent2", '<a:srgbClr val="ED7D31"/>'),
        ("accent3", '<a:srgbClr val="A5A5A5"/>'),
        ("accent4", '<a:srgbClr val="FFC000"/>'),
        ("accent5", '<a:srgbClr val="5B9BD5"/>'),
        ("accent6", '<a:srgbClr val="70AD47"/>'),
        ("hlink", '<a:srgbClr val="0563C1"/>'),
        ("folHlink", '<a:srgbClr val="954F72"/>'),
    ]
    clr = "".join(f"<a:{k}>{v}</a:{k}>" for k, v in colors)
    fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    fills = "".join(fill for _ in range(3))
    ln = ('<a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
          '<a:prstDash val="solid"/></a:ln>')
    effects = "".join('<a:effectStyle><a:effectLst/></a:effectStyle>' for _ in range(3))
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<a:theme xmlns:a="{_A}" name="QCC Neutral"><a:themeElements>'
        f'<a:clrScheme name="Neutral">{clr}</a:clrScheme>'
        f'<a:fontScheme name="Neutral"><a:majorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
        f'<a:minorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
        f'<a:fmtScheme name="Neutral"><a:fillStyleLst>{fills}</a:fillStyleLst>'
        f'<a:lnStyleLst>{ln + ln + ln}</a:lnStyleLst>'
        f'<a:effectStyleLst>{effects}</a:effectStyleLst>'
        f'<a:bgFillStyleLst>{fills}</a:bgFillStyleLst></a:fmtScheme>'
        f'</a:themeElements></a:theme>'
    )


def _core(title):
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        f'xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f'<dc:title>{_esc(title)}</dc:title><dc:creator>qcc-copilot</dc:creator></cp:coreProperties>'
    )


def _app(n):
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        f'<Application>qcc-copilot</Application><Slides>{n}</Slides></Properties>'
    )


def _xml_tags_balanced(text):
    """expat-free 标签配对检查（本环境 pyexpat 不可用）；不做完整 DTD/实体校验。"""
    import re

    stack = []
    for m in re.finditer(r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<\?.*?\?>|<!DOCTYPE[^>]*>|<[^>]+>", text, re.S):
        token = m.group(0)
        if token.startswith(("<!--", "<![CDATA", "<?", "<!")):
            continue
        if token.startswith("</"):
            name = re.match(r"</\s*([^\s>/]+)", token)
            if not name:
                return False, f"bad close tag {token!r}"
            n = name.group(1)
            if not stack or stack[-1] != n:
                return False, f"mismatched close {n}, open={stack[-1] if stack else None}"
            stack.pop()
        else:
            self_closing = token.rstrip().endswith("/>")
            name = re.match(r"<\s*([^\s>/]+)", token)
            if not name:
                return False, f"bad open tag {token!r}"
            if not self_closing:
                stack.append(name.group(1))
    if stack:
        return False, f"unclosed tags {stack}"
    return True, ""


def verify_pptx(path):
    """结构核验：zip 完整性、必需部件、标签配对；不等于独立渲染检查。"""
    report = {"path": str(path), "openable_zip": False, "parts": 0,
              "tags_balanced": True, "slides": 0, "errors": [],
              "check_kind": "structure_tags_balance (expat-free; not a rendering check)"}
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            bad = z.testzip()
            if bad is not None:
                report["errors"].append(f"corrupt zip entry: {bad}")
            report["openable_zip"] = True
            report["parts"] = len(names)
            report["slides"] = sum(
                1 for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")
            )
            required = ["[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml",
                        "ppt/slideMasters/slideMaster1.xml", "ppt/theme/theme1.xml"]
            for r in required:
                if r not in names:
                    report["errors"].append(f"missing part: {r}")
            for n in names:
                if n.endswith(".xml") or n.endswith(".rels"):
                    ok, err = _xml_tags_balanced(z.read(n).decode("utf-8"))
                    if not ok:
                        report["tags_balanced"] = False
                        report["errors"].append(f"unbalanced tags in {n}: {err}")
    except Exception as exc:
        report["errors"].append(f"cannot open zip: {exc}")
    report["xml_wellformed"] = report["tags_balanced"]
    report["structure_ok"] = (
        report["openable_zip"] and report["tags_balanced"] and not report["errors"]
    )
    return report
