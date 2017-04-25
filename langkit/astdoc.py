from __future__ import absolute_import, division, print_function

from langkit import compiled_types, documentation, expressions
from langkit.diagnostics import check_source_language, Severity
from langkit.utils import dispatch_on_type

try:
    from docutils.core import publish_parts
except ImportError:
    check_source_language(
        False,
        "Missing docutils to properly render sphinx doc. Install the "
        "docutils package",
        severity=Severity.warning
    )

    # Provide a stub implementation for publish_parts
    def publish_parts(x, *args, **kwargs):
        return {'html_body': x}


def escape(text):
    for char, entity in (
        ('<', '&lt;'), ('>', '&gt;'), ('&', '&amp;')
    ):
        text = text.replace(char, entity)
    return text


def trim_docstring_lines(docstring):
    """
    This function will return a trimmed version of the docstring, removing
    whitespace at the beginning of lines depending on the offset of the first
    line.

    :type docstring: str
    """

    # Remove leading newline if needed
    docstring = docstring.lstrip('\n')

    # Compute the offset
    offset = len(docstring) - len(docstring.lstrip(' '))

    # Check that the docstring is properly formed
    check_source_language(
        not docstring[offset].isspace(), "Malformed docstring"
    )

    # Trim every line of the computed offset value
    return '\n'.join(
        line[offset:]
        for line in docstring.splitlines()
    )


def format_doc(entity):
    doc = entity.doc()
    if doc:
        doc = trim_docstring_lines(doc)
        ret = '<div class="doc">{}</div>'.format(
            publish_parts(doc, writer_name='html')['html_body']
        )
        return ret
    else:
        return '<div class="disabled">No documentation</div>'.format(doc)


def print_struct(context, file, struct):
    is_astnode = struct.is_ast_node
    base = struct.base() if is_astnode else None
    fields = list(struct.get_abstract_fields())

    # Do not document internal fields unless everything is public
    if not context.library_fields_all_public:
        fields = [f for f in fields if not f.is_internal]

    descr = []
    if is_astnode:
        kind = 'node'
        if struct.abstract:
            descr.append('<span class="kw">abstract</span>')
        descr.append('<span class="kw">root</span>'
                     if base == compiled_types.ASTNode else
                     astnode_ref(base))
    else:
        kind = 'struct'
    print(
        '<dt id="{name}">'
        '<span class="kw">{kind}</span>'
        ' <span class="def">{name}</span>'
        '{descr}</dt>'.format(
            name=struct.name().camel,
            kind=kind,
            descr=' : {}'.format(' '.join(descr)) if descr else ''
        ),
        file=file
    )
    print('<dd>{}'.format(format_doc(struct)), file=file)

    print('<dl>', file=file)
    for f in fields:
        print_field(context, file, struct, f)

    print('</dl>', file=file)
    print('</dd>', file=file)


def print_field(context, file, struct, field):
    prefixes = []
    if field.is_private:
        prefixes.append('<span class="private">private</span>')
    prefixes.append('<span class="kw">{}</span>'.format(
        dispatch_on_type(type(field), (
            (compiled_types.AbstractField, lambda _: 'field'),
            (expressions.PropertyDef, lambda _: 'property')
        )),
    ))

    is_inherited = field.struct != struct

    inherit_note = (
        ' [inherited from {}]'.format(field_ref(field))
        if is_inherited else ''
    )

    div_classes = ['node_wrapper']
    if is_inherited:
        div_classes.append('field_inherited')
    if field.is_private:
        div_classes.append('field_private')

    print('<div class="{}">'.format(' '.join(div_classes)), file=file)
    print(
        '<dt>{prefixes}'
        ' <span class="def" id="{node}-{field}">{field}</span>'
        ' : {type}{inherit_note}</dt>'.format(
            prefixes=' '.join(prefixes),
            node=struct.name().camel,
            field=field.name.lower,
            type=(
                astnode_ref(field.type)
                if field.type in context.astnode_types else
                field.type.name().camel
            ),
            inherit_note=inherit_note
        ),
        file=file
    )
    # Don't repeat the documentation for inheritted fields
    if field.struct == struct:
        print('<dd>{}</dd>'.format(format_doc(field)), file=file)

    print('</div>', file=file)


def astnode_ref(node):
    return '<a href="#{name}" class="ref-link">{name}</a>'.format(
        name=node.name().camel
    )


def field_ref(field):
    return '<a href="#{node}-{field}" class="ref-link">{node}</a>'.format(
        node=field.struct.name().camel,
        field=field.name.lower
    )


ASTDOC_CSS = """
html {
    background-color: rgb(8, 8, 8);
    color: rgb(248, 248, 242);
    font-family: sans-serif;
}
.kw  { color: rgb(255, 95, 135); font-weight: bold; }
.private  { color: rgb(255, 130, 20); font-weight: bold; }
.def { color: rgb(138, 226, 52); font-weight: bold; }
.ref { color: rgb(102, 217, 239); }
.ref-link { color: rgb(102, 217, 239); text-decoration: underline; }
.disabled { color: rgb(117, 113, 94); font-style: italic;}
.doc { width: 600px; }
dt { font-family: monospace; }

.sidenav {
    height: 100%;
    width: 0;
    position: fixed;
    z-index: 1;
    top: 0;
    left: 0;
    background-color: #111;
    overflow-x: hidden;
    padding-top: 60px;
    width: 250px;
}

.sidenav a {
    padding: 8px 8px 8px 32px;
    text-decoration: none;
    font-size: 25px;
    color: #818181;
    display: block;
    transition: 0.3s
}

#main {
    padding: 20px;
    margin-left: 250px;
}

@media screen and (max-height: 450px) {
    .sidenav {padding-top: 15px;}
    .sidenav a {font-size: 18px;}
}
""".strip()

ASTDOC_JS = """
<script>
function trigger_elements(cat) {
    var btn = document.getElementById('btn_show_' + cat);
    nodes = [...document.querySelectorAll('.field_' + cat)]
    if (btn.text === "Show " + cat) {
        btn.text = "Hide " + cat;
        nodes.forEach((n) => { n.style.display = "block"; })
    } else {
        btn.text = "Show " + cat;
        nodes.forEach((n) => { n.style.display = "none"; })
    }
}
</script>
"""


ASTDOC_HTML = """<html>
<head>
    <title>{lang_name} - AST documentation</title>
    <style type="text/css">{css}</style>
</head>
<body>
    {js}
    <div id="mySidenav" class="sidenav">
      <a id="btn_show_inherited" href="javascript:void(0)"
       onclick="trigger_elements('inherited')">Hide inherited</a>
      <a id="btn_show_private" href="javascript:void(0)"
       onclick="trigger_elements('private')">Hide private</a>
    </div>
    <div id="main">
    <h1>{lang_name} - AST documentation</h1>
"""


def write_astdoc(context, file):
    """
    Generate a synthetic HTML documentation about AST nodes and types.

    :param context: Compile context to provide the AST nodes to document.
    :type context: langkit.compile_context.CompileCtx

    :param file file: Output file for the documentation.
    """
    print(ASTDOC_HTML.format(
        lang_name=context.lang_name.camel,
        css=ASTDOC_CSS,
        js=ASTDOC_JS
    ), file=file)

    if context.enum_types:
        print('<h2>Enumeration types</h2>', file=file)

        for enum_type in context.enum_types:
            print('enum {}:'.format(enum_type.name().camel), file=file)
            doc = enum_type.doc()
            if doc:
                print(documentation.format_text(doc, 4), file=file)
            print('    {}'.format(' '.join(enum_type.alternatives)),
                  file=file)
            print('', file=file)

    if context.struct_types:
        print('<h2>Structure types</h2>', file=file)

        print('<dl>', file=file)
        for struct_type in context.struct_types:
            print_struct(context, file, struct_type)
        print('</dl>', file=file)

    print('<h2>AST node types</h2>', file=file)

    print('<dl>', file=file)
    for typ in context.astnode_types:
        print_struct(context, file, typ)
    print('</dl>', file=file)
    print('</div></body></html>', file=file)
