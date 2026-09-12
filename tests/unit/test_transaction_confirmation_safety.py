from __future__ import annotations

import ast
from pathlib import Path


SOURCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "chatbot"
    / "orchestrator.py"
)


def _tree():
    return ast.parse(
        SOURCE_PATH.read_text()
    )


def _function(
    tree: ast.AST,
    name: str,
) -> ast.AsyncFunctionDef:

    return next(
        node
        for node
        in ast.walk(tree)
        if (
            isinstance(
                node,
                ast.AsyncFunctionDef,
            )
            and
            node.name == name
        )
    )


def _mutation_helper(
    tree: ast.AST,
    method: str,
) -> ast.AsyncFunctionDef:

    matches = []

    for function in ast.walk(tree):

        if not isinstance(
            function,
            ast.AsyncFunctionDef,
        ):
            continue

        if any(
            (
                isinstance(node, ast.Call)
                and
                isinstance(
                    node.func,
                    ast.Attribute,
                )
                and
                node.func.attr == method
            )
            for node
            in ast.walk(function)
        ):
            matches.append(function)

    assert len(matches) == 1

    return matches[0]


def _parent_map(
    tree: ast.AST,
):
    result = {}

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(
            parent
        ):
            result[child] = parent

    return result


def _conditions(
    node: ast.AST,
    *,
    parent_map,
    stop,
) -> str:

    values = []

    current = parent_map.get(node)

    while current is not None:

        if isinstance(
            current,
            ast.If,
        ):
            values.append(
                ast.unparse(
                    current.test
                )
            )

        if current is stop:
            break

        current = parent_map.get(
            current
        )

    return " ".join(values)


def test_booking_mutation_requires_explicit_confirmation():
    tree = _tree()

    handle = _function(
        tree,
        "handle_conversation",
    )

    parent_map = _parent_map(
        tree
    )

    calls = [
        node
        for node
        in ast.walk(handle)
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
            "confirm_booking"
        )
    ]

    assert len(calls) == 1

    conditions = _conditions(
        calls[0],
        parent_map=parent_map,
        stop=handle,
    )

    assert "pending_booking" in conditions
    assert "CONFIRM_PHRASES" in conditions
    assert any(
        keyword.arg == "hospital_id"
        for keyword
        in calls[0].keywords
    )


def test_cancel_and_reschedule_require_confirm_and_tenant():
    tree = _tree()

    handle = _function(
        tree,
        "handle_conversation",
    )

    parent_map = _parent_map(
        tree
    )

    for method in (
        "cancel_appointment",
        "reschedule_appointment",
    ):

        helper = _mutation_helper(
            tree,
            method,
        )

        parameters = {
            arg.arg
            for arg
            in (
                helper.args.posonlyargs
                +
                helper.args.args
                +
                helper.args.kwonlyargs
            )
        }

        assert "hospital_id" in parameters

        service_calls = [
            node
            for node
            in ast.walk(helper)
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
                node.func.attr == method
            )
        ]

        assert len(service_calls) == 1

        assert any(
            keyword.arg == "hospital_id"
            for keyword
            in service_calls[0].keywords
        )

        helper_calls = [
            node
            for node
            in ast.walk(handle)
            if (
                isinstance(
                    node,
                    ast.Call,
                )
                and
                (
                    (
                        isinstance(
                            node.func,
                            ast.Name,
                        )
                        and
                        node.func.id
                        ==
                        helper.name
                    )
                    or
                    (
                        isinstance(
                            node.func,
                            ast.Attribute,
                        )
                        and
                        node.func.attr
                        ==
                        helper.name
                    )
                )
            )
        ]

        assert len(helper_calls) == 1

        assert any(
            keyword.arg == "hospital_id"
            for keyword
            in helper_calls[0].keywords
        )

        conditions = _conditions(
            helper_calls[0],
            parent_map=parent_map,
            stop=handle,
        )

        assert "pending_action" in conditions
        assert "CONFIRM_PHRASES" in conditions


def test_pending_action_has_abort_path_without_mutation():
    tree = _tree()

    handle = _function(
        tree,
        "handle_conversation",
    )

    abort_ifs = []

    for node in ast.walk(handle):

        if not isinstance(
            node,
            ast.If,
        ):
            continue

        rendered = ast.unparse(
            node.test
        )

        if (
            "pending_action" in rendered
            and
            "ABORT_PHRASES" in rendered
        ):
            abort_ifs.append(node)

    assert len(abort_ifs) >= 1

    for node in abort_ifs:

        mutation_calls = [
            call
            for call
            in ast.walk(node)
            if (
                isinstance(
                    call,
                    ast.Call,
                )
                and
                isinstance(
                    call.func,
                    ast.Attribute,
                )
                and
                call.func.attr
                in {
                    "cancel_appointment",
                    "reschedule_appointment",
                    "confirm_booking",
                }
            )
        ]

        assert not mutation_calls
