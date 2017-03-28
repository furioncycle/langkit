## vim: filetype=makoada

--  Start row_code

${pos} := ${pos_name};

## This is the main body of the row, which is the concatenation of the code for
## each row part.
% for (subp, subres) in zip(parser.parsers, parser.subresults):

<% parser_context = subp.gen_code_or_fncall(pos) %>

## Parse the element
${parser_context.code}

## If the parsing was successful then
if ${parser_context.pos_var_name} /= No_Token_Index then

   ## Set current position to the out position of the parsed row element
   ${pos} := ${parser_context.pos_var_name};

   ## Store the result if it is not discarded
   % if not subp.discard():
      ${subres} := ${parser_context.res_var_name};
   % endif

else
   ## If the parsing was unsuccessful, then set the position accordingly
   ## and then skip the rest of the row parsing.
   ${pos} := No_Token_Index;
   goto ${exit_label}_0;

end if;
% endfor

pragma Warnings (Off, "referenced");
<<${exit_label}_0>>
pragma Warnings (On, "referenced");

--  End row_code
