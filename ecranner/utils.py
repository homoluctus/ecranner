def exception_exists(results):
    """Calculate the number of exceptions in the argument 'results'

    Args:
        results (list)

    Retuns:
        the number of exceptions in results
    """

    if not isinstance(results, list):
        raise TypeError(
            f'Expected type is list, but the argument type is {type(results)}'
        )

    exc = list(filter(
        lambda result: isinstance(result, Exception), results)
    )
    return len(list(exc))
