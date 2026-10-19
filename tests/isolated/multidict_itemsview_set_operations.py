import gc

import objgraph  # type: ignore[import-untyped]

from multidict import CIMultiDict, MultiDict


class SubtractionValue:
    pass


class ReflectedUnionValue:
    pass


class SubtractionOperandValue:
    pass


class ReflectedUnionOperandValue:
    pass


class XorOperandValue:
    pass


class HashError(Exception):
    pass


class HashFailingOperandValue:
    def __hash__(self) -> int:
        raise HashError


def _run_isolated_case() -> None:
    for _ in range(100):
        subtraction_value = SubtractionValue()
        subtraction_md = MultiDict([("key", subtraction_value)])
        subtraction_result = subtraction_md.items() - set()
        del subtraction_result, subtraction_md, subtraction_value

    for _ in range(100):
        reflected_union_value = ReflectedUnionValue()
        reflected_union_md = MultiDict([("key", reflected_union_value)])
        reflected_union_result = set() | reflected_union_md.items()
        del reflected_union_result, reflected_union_md, reflected_union_value

    # Non-empty operands exercise the loop parsing the operand's items.
    for md_cls in (MultiDict, CIMultiDict):
        md = md_cls([("key", "value")])
        for i in range(100):
            sub_operand = [(f"k{i}", SubtractionOperandValue())]
            sub_result = md.items() - sub_operand
            union_operand = [(f"k{i}", ReflectedUnionOperandValue())]
            union_result = union_operand | md.items()
            del sub_operand, sub_result, union_operand, union_result

    # Symmetric difference subtracts the operand from the items view
    # internally, going through the same operand-parsing loop.
    for md_cls in (MultiDict, CIMultiDict):
        md = md_cls([("key", "value")])
        for i in range(100):
            xor_operand = [(f"k{i}", XorOperandValue())]
            xor_result = md.items() ^ xor_operand
            del xor_operand, xor_result

    # An operand item failing mid-iteration must not leak the item itself.
    for md_cls in (MultiDict, CIMultiDict):
        md = md_cls([("key", "value")])
        for i in range(100):
            failing_operand = [(f"k{i}", HashFailingOperandValue())]
            try:
                md.items() - failing_operand
            except HashError:
                pass
            else:
                raise AssertionError("HashError not raised")
            del failing_operand

    gc.collect()
    leaked_subtraction = len(objgraph.by_type("SubtractionValue"))
    leaked_reflected_union = len(objgraph.by_type("ReflectedUnionValue"))
    leaked_subtraction_operand = len(objgraph.by_type("SubtractionOperandValue"))
    leaked_reflected_union_operand = len(objgraph.by_type("ReflectedUnionOperandValue"))
    leaked_xor_operand = len(objgraph.by_type("XorOperandValue"))
    leaked_hash_failing_operand = len(objgraph.by_type("HashFailingOperandValue"))
    assert leaked_subtraction == 0, (
        f"{leaked_subtraction} subtraction values not collected by GC"
    )
    assert leaked_reflected_union == 0, (
        f"{leaked_reflected_union} reflected union values not collected by GC"
    )
    assert leaked_subtraction_operand == 0, (
        f"{leaked_subtraction_operand} subtraction operand values not collected by GC"
    )
    assert leaked_reflected_union_operand == 0, (
        f"{leaked_reflected_union_operand} reflected union operand values "
        "not collected by GC"
    )
    assert leaked_xor_operand == 0, (
        f"{leaked_xor_operand} symmetric difference operand values "
        "not collected by GC"
    )
    assert leaked_hash_failing_operand == 0, (
        f"{leaked_hash_failing_operand} failing subtraction operand values "
        "not collected by GC"
    )


if __name__ == "__main__":
    _run_isolated_case()
