"""
Module: Design Calculator Functionality
Description: Define the mathematical operations (addition, subtraction, multiplication, division) that the calculator will perform and create a plan for implementing these operations in Python.
Generated: 2025-06-21 13:32:49
"""

def power(self, base, exponent):
    """
    Calculates the power of a number.

    Args:
        base (float): The base.
        exponent (float): The exponent.

    Returns:
        float: The result of raising the base to the power of the exponent.
    """
    logging.info("Performing exponentiation")
    try:
        result = base ** exponent
        return result
    except Exception as e:
        logging.error(str(e))
        return None