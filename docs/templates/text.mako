## Define mini-templates for each portion of the doco.

<%!
  def indent(s, spaces=4):
      new = s.replace('\n', '\n' + ' ' * spaces)
      return ' ' * spaces + new.strip()
%>

<%def name="deflist(s)">:${indent(s)[1:]}</%def>

<%def name="h3(s)">### ${s}
</%def>

<%def name="h4(s)">#### ${s}
</%def>

<%def name="function(func)" buffered="True">
```python
    <%
        returns = show_type_annotations and func.return_annotation() or ''
        if returns:
            returns = ' -> ' + returns
    %>
`${func.name}(${", ".join(func.params(annotate=show_type_annotations))})${returns}`
${func.docstring | deflist}
```
</%def>

<%def name="variable(var)" buffered="True">
`${var.name}`
${var.docstring | deflist}
</%def>

<%def name="class_(cls)" buffered="True">
`${cls.name}(${", ".join(cls.params(annotate=show_type_annotations))})`
${cls.docstring | deflist}
<%
  class_vars = cls.class_variables(show_inherited_members, sort=sort_identifiers)
  static_methods = cls.functions(show_inherited_members, sort=sort_identifiers)
  inst_vars = cls.instance_variables(show_inherited_members, sort=sort_identifiers)
  methods = cls.methods(show_inherited_members, sort=sort_identifiers)
  mro = cls.mro()
  subclasses = cls.subclasses()
%>
## % if mro:
##     ${h3('Ancestors (in MRO)')}
##     % for c in mro:
##     * ${c.refname}
##     % endfor
##
## % endif
% if subclasses:
    ${h3('Descendants')}
    % for c in subclasses:
    * ${c.refname}
    % endfor

% endif
% if class_vars:
    ${h3('Class variables')}
    % for v in class_vars:
```python
${variable(v)}
```

    % endfor
% endif
% if static_methods:
    ${h3('Static methods')}
    % for f in static_methods:
```python
${function(f)}
```

    % endfor
% endif
% if inst_vars:
    ${h3('Instance variables')}
    % for v in inst_vars:
```python
${variable(v)}
```

    % endfor
% endif
% if methods:
    ${h3('Methods')}
    % for m in methods:
```python
${function(m)}
```

    % endfor
% endif
</%def>

## Start the output logic for an entire module.

<%
  variables = module.variables()
  classes = module.classes()
  functions = module.functions()
  submodules = module.submodules()
  heading = 'Namespace' if module.is_namespace else 'Module'
%>

---
path: "/modules/${module.name}"
title: "${module.name}"
section: "modules"
---

${heading} ${module.name}
=${'=' * (len(module.name) + len(heading))}
${module.docstring}


% if submodules:
${h4("Sub-modules")}
    % for m in submodules:
* ${m.name}
    % endfor
% endif

% if variables:
${h4("Variables")}
    % for v in variables:
${variable(v)}

    % endfor
% endif

% if functions:
${h4("Functions")}
    % for f in functions:
${function(f)}

    % endfor
% endif

% if classes:
${h4("Classes")}
    % for c in classes:
${class_(c)}

    % endfor
% endif
