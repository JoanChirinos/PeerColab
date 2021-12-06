"""
PeerColab

Helper functions for the main Flask file

Copyright Joan Chirinos, 2021.
"""


def verify_auth_args(*args: str) -> bool:
    """
    Verify arguments from user-inputted authentication forms

    Parameters
    ----------
    *args : str
        The non-keyworded arguments to verify

    Returns
    -------
    bool
        True if all form elemens are valid.
        False otherwise.

    """
    # TODO: Robustify. Possibly using **kwargs and arg-specific verification
    # TODO: Return some sequence or mapping corresponding to which args are
    #       invalid
    for arg in args:
        if len(arg.strip()) == 0 or arg.strip() != arg:
            return False
    return True
