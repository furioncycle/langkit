## vim: filetype=makoada

<%namespace name="scopes"  file="scopes_ada.mako" />
<%namespace name="helpers" file="helpers.mako" />

% if not property.abstract:
${"overriding" if property.overriding else ""} function ${property.name}
  ${helpers.argument_list(property, property.dispatching)}
   return ${property.type.name()}
is
   use type AST_Envs.Lexical_Env;

   pragma Warnings (Off, "is not referenced");
   ## We declare a variable Self, that has the named class wide access type
   ## that we can use to dispatch on other properties and all.
   Self : ${Self.type.name()} := ${Self.type.name()}
     (${property.self_arg_name});

   ## Properties are evaluated in the context of a lexical environment. If none
   ## was passed to the property, we assume that the users want to evaluate it
   ## in the context of the scope of the node.
   Current_Env : AST_Envs.Lexical_Env :=
     (if ${property.env_arg_name} /= null
      then ${property.env_arg_name}
      else Node.Self_Env);
   pragma Warnings (On, "is not referenced");

   Property_Result : ${property.type.name()} := ${property.type.nullexpr()};

   ## For each scope, there is one of the following subprograms that finalizes
   ## all the ref-counted local variables it contains, excluding variables from
   ## children scopes.
   <% all_scopes = property.vars.all_scopes %>
   % for scope in all_scopes:
      % if scope.has_refcounted_vars():
         procedure ${scope.finalizer_name};
      % endif
   % endfor

   ${property.vars.render()}

   % for scope in all_scopes:
      % if scope.has_refcounted_vars():
         procedure ${scope.finalizer_name} is
         begin
            ## Finalize the local variable for this scope
            % for var in scope.variables:
               % if var.type.is_refcounted():
                  Dec_Ref (${var.name});
               % endif
            % endfor
         end ${scope.finalizer_name};
      % endif
   % endfor

begin
   ${property.constructed_expr.render_pre()}

   Property_Result := ${property.constructed_expr.render_expr()};
   % if property.type.is_refcounted():
      Inc_Ref (Property_Result);
   % endif
   ${scopes.finalize_scope(property.vars.root_scope)}

   return Property_Result;

% if property.vars.root_scope.has_refcounted_vars(True):
   exception
      when Property_Error =>
         % for scope in all_scopes:
            % if scope.has_refcounted_vars():
               ${scope.finalizer_name};
            % endif
         % endfor
         raise;
% endif
end ${property.name};
% endif
