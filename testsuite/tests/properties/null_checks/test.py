"""
Test that property checks are properly emitted when null checks should trigger
them.
"""

from __future__ import absolute_import, division, print_function

import os.path

from langkit.diagnostics import Diagnostics
from langkit.dsl import (AnalysisUnitType, ASTNode, Field, T, TokenType,
                         abstract)
from langkit.expressions import No, Property, Self
from langkit.parsers import Grammar, Or, Row, Tok

from lexer_example import Token
from utils import build_and_run


Diagnostics.set_lang_source_dir(os.path.abspath(__file__))


class FooNode(ASTNode):
    null_unit = Property(No(AnalysisUnitType), public=True)
    null_node = Property(No(T.Expression.entity), public=True)

    deref_null_unit = Property(Self.null_unit.root.as_bare_entity, public=True)
    deref_null_node = Property(Self.null_node.null_node,
                               public=True)
    null_node_unit = Property(Self.null_node.unit, public=True)

    cast_null_node = Property(Self.null_node.cast(T.Name), public=True)

    match_null_node = Property(
        Self.null_node.el.match(
            lambda l=T.Literal: l,
            lambda n=T.Name: n,
            lambda others: others
        ).as_bare_entity,
        public=True
    )


@abstract
class Expression(FooNode):
    pass


class Literal(Expression):
    tok = Field(type=TokenType)


class Name(Expression):
    tok = Field(type=TokenType)

    env_element = Property(Self.children_env.get(Self.tok.symbol).at(0))
    deref_env_element = Property(Self.env_element.null_node, public=True)
    match_env_element = Property(
        Self.env_element.match(
            lambda l=T.Literal.entity: l,
            lambda n=T.Name.entity: n,
            lambda others: others,
        ),
        public=True
    )


class Plus(Expression):
    left = Field()
    right = Field()


foo_grammar = Grammar('main_rule')
foo_grammar.add_rules(
    main_rule=foo_grammar.expression,
    expression=Or(
        Row('(', foo_grammar.expression, ')')[1],
        Plus(foo_grammar.atom, '+', foo_grammar.main_rule),
        foo_grammar.atom,
    ),
    atom=Or(
        Row(Tok(Token.Number, keep=True)) ^ Literal,
        Row(Tok(Token.Identifier, keep=True)) ^ Name,
    ),
)
build_and_run(foo_grammar, 'main.py')
print('Done')
