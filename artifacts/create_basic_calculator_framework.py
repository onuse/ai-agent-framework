"""
Task: Create Basic Calculator Framework
Description: Establish the basic structure for the calculator, including input validation and a method to perform calculations. This will be a bare-bones implementation without any functionality.
Generated: 2025-06-21 13:08:46
"""

import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO)

class Calculator:
    """
    A basic calculator class with methods for addition, subtraction, multiplication, and division.
    """

    def add(self, num1, num2):
        """
        Adds two numbers.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The sum of the two numbers.
        """
        logging.info("Performing addition")
        try:
            result = num1 + num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def subtract(self, num1, num2):
        """
        Subtracts the second number from the first.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The difference between the two numbers.
        """
        logging.info("Performing subtraction")
        try:
            result = num1 - num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def multiply(self, num1, num2):
        """
        Multiplies two numbers.

        Args:
            num1 (float): The first number.
            num2 (float): The second number.

        Returns:
            float: The product of the two numbers.
        """
        logging.info("Performing multiplication")
        try:
            result = num1 * num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None

    def divide(self, num1, num2):
        """
        Divides the first number by the second.

        Args:
            num1 (float): The dividend.
            num2 (float): The divisor.

        Returns:
            float: The quotient of the two numbers.
        """
        logging.info("Performing division")
        try:
            if num2 == 0:
                raise ZeroDivisionError
            result = num1 / num2
            return result
        except TypeError:
            logging.error("Invalid input type. Please enter numbers only.")
            return None
        except ZeroDivisionError:
            logging.error("Cannot divide by zero")
            return None


# Example usage:
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(10, 5))  # Output: 15
    print(calc.subtract(10, 5))  # Output: 5
    print(calc.multiply(10, 5))  # Output: 50
    print(calc.divide(10, 2))  # Output: 5.0