from __future__ import annotations

import ast
from pathlib import Path


PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "chatbot"
    / "orchestrator.py"
)


def _functions(
    tree: ast.AST,
):
    return {
        node.name: node
        for node
        in ast.walk(tree)
        if isinstance(
            node,
            ast.AsyncFunctionDef,
        )
    }


def _parameters(
    fn: ast.AsyncFunctionDef,
):
    return {
        arg.arg
        for arg
        in (
            fn.args.posonlyargs
            +
            fn.args.args
            +
            fn.args.kwonlyargs
        )
    }


def _parents(
    tree: ast.AST,
):
    result = {}

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(
            parent
        ):
            result[
                child
            ] = parent

    return result


def _enclosing(
    node,
    parents,
):

    current = parents.get(
        node
    )

    while current is not None:

        if isinstance(
            current,
            ast.AsyncFunctionDef,
        ):
            return current

        current = parents.get(
            current
        )

    return None


def test_list_for_phone_is_always_hospital_scoped():

    source = PATH.read_text()

    tree = ast.parse(
        source
    )

    parents = _parents(
        tree
    )

    calls = [
        node
        for node
        in ast.walk(tree)
        if (
            isinstance(
                node,
                ast.Call,
            )
            and
            isinstance(
                node.func,
                ast.Attribute,
            )
            and
            node.func.attr
            ==
            "list_for_phone"
        )
    ]

    assert calls

    for call in calls:

        assert any(
            keyword.arg
            ==
            "hospital_id"
            for keyword
            in call.keywords
        )

        fn = _enclosing(
            call,
            parents,
        )

        assert fn is not None

        assert (
            "hospital_id"
            in _parameters(
                fn
            )
        )


def test_refresh_wrappers_receive_hospital_id_at_callsites():

    source = PATH.read_text()

    tree = ast.parse(
        source
    )

    functions = _functions(
        tree
    )

    parents = _parents(
        tree
    )

    service_calls = [
        node
        for node
        in ast.walk(tree)
        if (
            isinstance(
                node,
                ast.Call,
            )
            and
            isinstance(
                node.func,
                ast.Attribute,
            )
            and
            node.func.attr
            ==
            "list_for_phone"
        )
    ]

    wrappers = {
        _enclosing(
            call,
            parents,
        ).name
        for call
        in service_calls
    }

    for wrapper in wrappers:

        for fn in functions.values():

            calls = [
                call
                for call
                in ast.walk(fn)
                if (
                    isinstance(
                        call,
                        ast.Call,
                    )
                    and
                    (
                        (
                            isinstance(
                                call.func,
                                ast.Name,
                            )
                            and
                            call.func.id
                            ==
                            wrapper
                        )
                        or
                        (
                            isinstance(
                                call.func,
                                ast.Attribute,
                            )
                            and
                            call.func.attr
                            ==
                            wrapper
                        )
                    )
                )
            ]

            for call in calls:

                assert any(
                    keyword.arg
                    ==
                    "hospital_id"
                    for keyword
                    in call.keywords
                )
